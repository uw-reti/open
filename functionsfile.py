# -*- coding: utf-8 -*-
"""
BL TODOs:
    - At the moment build_cost is not variable (needs target and actual)
    - add in liquidated damage % per year option? -> that way we can better quantify losses for being behind schedule
"""

import numpy as np


class PDSystems:

    """for ALL functions --> defining input names"""
    def __init__(self, inputs):
        self.inputs = inputs
        
        # unpack inputs
        self.design_time = inputs["design_time"]
        self.build_time = inputs["build_time"]
        self.operating_time = inputs["operating_time"]
        self.commission_time = inputs["commission_time"]

        self.design_cost = inputs["design_cost"]
        self.build_cost = inputs["build_cost"]
        self.revenue_per_year = inputs["revenue_per_year"]
        self.OM_per_year = inputs["om_per_year"]

        self.discount_rate = inputs["discount_rate"]
        self.contingency = inputs["contingency"]
        self.profit_margin = inputs["profit_margin"]

        self.actual_design_progress = np.array(inputs["actual_design_progress"])
        self.actual_build_progress = np.array(inputs["actual_build_progress"])
        self.target_design_progress = np.array(inputs["target_design_progress"])
        self.target_build_progress = np.array(inputs["target_build_progress"])

        self.percent_design = inputs["percent_design"]
        self.percent_build = inputs["percent_build"]
        self.percent_OM_to = inputs["percent_OM_to"]
        self.percent_revenue_to = inputs["percent_revenue_to"]

        self.actors = ["vendor", "AE", "constructor", "utility"]


        self.target_year = np.arange(0, self.design_time + self.build_time + self.commission_time + self.operating_time)
        self.actual_design_time = len(self.actual_design_progress)
        self.actual_build_time = len(self.actual_build_progress)
        self.actual_year = np.arange(0, self.actual_design_time + self.actual_build_time + self.commission_time + self.operating_time)
        
        self.target_progress = np.append(self.target_design_progress, self.target_build_progress)
        self.actual_progress = np.append(self.actual_design_progress, self.actual_build_progress)

        self.full_progress_array = np.zeros_like(self.actual_year)
        end_index = len(self.actual_progress)
        self.full_progress_array[:end_index] = self.actual_progress
        #print(self.full_progress_array)
        """start_index = 0
        end_index = start_index + actual_progress.shape[0]
        progress_array[start_index:end_index] = actual_progress"""

        #Setup masks
        self.mask_design = self.actual_year < self.actual_design_time
        self.mask_build = (
            (self.actual_year >= self.actual_design_time)
            & (self.actual_year < self.actual_design_time + self.actual_build_time)
        )
        self.mask_om = self.actual_year >= (self.actual_design_time + self.actual_build_time)
        #mask_design = year < actual_design_time
        #mask_build = (year >= actual_design_time) & (year < actual_design_time + actual_build_time)
        #mask_om = year >= (actual_design_time + actual_build_time)

        #Dictionaries for payouts
        self.om_costs = {}
        
        self.nondisc_costs = {}
        self.disc_costs = {}
        self.net_disc = {}

        self.fp_nondisc_revenue = {}
        self.fp_disc_revenue = {}
        self.fp_design_payout_amount={}
        self.fp_build_payout_amount={}

        self.cp_disc_costs = {}
        self.cp_nondisc_revenue = {}
        self.cp_disc_revenue = {}
        self.cp_nondisc_operating_revenue = {}
        self.cp_disc_operating_revenue = {}

        self.ipd_disc_costs = {}
        self.ipd_nondisc_revenue = {}
        self.ipd_disc_revenue = {}

        self.NPV_timepath = {}
        self.cost_timepath = {}
        self.revenue_timepath = {}
        self.NPV = {}


    #fxn that returns the first index where progress >= 100; else return None
    def completion_index(self,full_progress_array):
        idx = np.where(full_progress_array >= 100)[0]
        return int(idx[0]) if idx.size > 0 else None

    """think I'm gonna get rid of this too"""
    #fxn that maps a sample index i (0-based) from a progress array of length n_years into a year within the phase: an integer in [phase_start, phase_start + phase_length - 1]
    def map_sample_to_phase_year(self,i, n_year, phase_start, phase_length):
        if n_year <= 0:
            raise ValueError("years must be > 0")
        frac = (i + 1) / n_year
        year_within = int(np.ceil(frac * phase_length)) - 1
        year_within = max(0, min(phase_length - 1, year_within))
        return int(phase_start + year_within)

    """think I'm gonna get rid of this bc it wasn't mapping properly"""
    #fxn that maps a cumulative progress (0..100%) to an absolute model year within the phase: an integer in [phase_start, phase_start + phase_length - 1]
    def map_cumulative_progress_to_phase_year(self, cum_pct, phase_start, phase_length):
        """Uses the same spacing rule as map_sample_to_phase_year but with completion
        fraction p = cum_pct/100 instead of p = (i+1)/n_years. Cash tied to *earned*
        progress moves to later phase years when the actual curve is back-loaded,
        so discounted NPV reflects delay (closer in spirit to fixed-price milestone timing).

        Costs may still use map_sample_to_phase_year if you keep distribute_progress_costs unchanged."""
        if phase_length <= 0:
            raise ValueError("phase_length must be > 0")
        p = float(np.clip(np.asarray(cum_pct, dtype=float), 0.0, 100.0)) / 100.0
        pl = int(phase_length)
        year_within = int(np.ceil(p * pl)) - 1
        year_within = max(0, min(pl - 1, year_within))
        return int(phase_start + year_within)

    #fxn that returns the absolute year when build progress reaches 100% (map sample index to a year). If build never reaches 100%, returns None
    def build_completion_payout_year(self, actual_build_progress, actual_design_time, actual_build_time):
        idx = self.completion_index(actual_build_progress)
        if idx is None:
            return None
        
        # position fraction within build
        frac = (idx + 1) / self.actual_build_time
        year_within = int(np.ceil(frac * actual_build_time))  # 1..build_time
        year_within = max(1, min(actual_build_time, year_within))
        payout_year = actual_design_time + year_within
        return payout_year


    """moved this up bc trying to keep consistent through cost+ and ipd and don't need duplicate now"""
    def distribute_progress_costs(self, full_progress_array, phase_cost, phase_start, phase_length, shares):
        """Convert a cumulative progress array (percent 0..100) into an annual payment array for each party in shares (dict with keys e.g. 'vendor','AE','constructor','utility').
        Returns dict of arrays (same length as 'year' timeline). Payment for each party = delta_progress_fraction * phase_cost * party_share.
        delta_progress_fraction = (progress[i] - progress[i-1]) / 100, with progress[-1]=0. Each delta is assigned to the mapped year computed by map_sample_to_phase_year. """
        
        self.n_year = len(full_progress_array)
        self.costs = {k: np.zeros_like(self.actual_year, dtype=float) for k in shares.keys()}
        """from ben"""
        self.cum_progress_frac = full_progress_array / 100.0
        self.delta_cum_progress_frac = np.concatenate(([self.cum_progress_frac[0]], np.diff(self.cum_progress_frac)))

        for i in range(self.n_year):
            # which year to assign this sample's payment to
            #self.pay_year = self.map_sample_to_phase_year(self, i, n_year, phase_start, phase_length)
            #changed this bc it was only calculating build costs at years 4 and 5 (mapping mightve been the problem)
            self.pay_year = phase_start + i
            # guard: if pay_year outside timeline, cap to last year
            #if pay_year < 0:
            #    pay_year = 0
            if self.pay_year >= len(self.actual_year):
                continue

            for actor, share in shares.items():
                self.costs[actor][self.pay_year] += self.delta_cum_progress_frac[i] * phase_cost * share
                #print("CP non disc costs:", actor, pay_year, delta_cum_progress_frac[i] * phase_cost * share)
        return self.costs


    """also moved this up bc trying to keep consistent through cost+ and ipd and don't need duplicate now"""
    def distribute_progress_payments(self, full_progress_array, phase_cost, phase_start, phase_length, shares):
        """Convert a cumulative progress array (percent 0..100) into an annual payment array for each party in shares (dict with keys e.g. 'vendor','AE','constructor','utility').
        Returns dict of arrays (same length as 'year' timeline). Payment for each party = delta_progress_fraction * phase_cost * party_share.
        delta_progress_fraction = (progress[i] - progress[i-1]) / 100. Each increment is booked to the phase year when cumulative progress reaches progress[i]
        (map_cumulative_progress_to_phase_year), so delayed/back-loaded curves move cash later vs index-only mapping."""
        
        self.n_year = len(full_progress_array)
        self.payments = {k: np.zeros_like(self.actual_year, dtype=float) for k in shares.keys()}
        self.cum_progress_frac = full_progress_array / 100.0
        #print(self.cum_progress_frac)
        self.delta_cum_progress_frac = np.concatenate(([self.cum_progress_frac[0]], np.diff(self.cum_progress_frac)))
        #print(self.delta_cum_progress_frac)

        for i in range(self.n_year):
            # Pay this increment when cumulative actual progress reaches progress_array[i] (not by sample index alone).
            """TODO: may need to change this to self.pay_year = phase_start + i too (look above)"""
            #self.pay_year = self.map_cumulative_progress_to_phase_year(full_progress_array[i], phase_start, phase_length)
            self.pay_year = phase_start + i
            # guard: if pay_year outside timeline, cap to last year
            #if pay_year < 0:
            #    pay_year = 0
            if self.pay_year >= len(self.actual_year):
                continue

            for actor, share in shares.items():
                self.payments[actor][self.pay_year] += self.delta_cum_progress_frac[i] * phase_cost * share
                #print("CP non disc payments:", actor, pay_year, delta_cum_progress_frac[i] * phase_cost * share)

            #print("progress =", full_progress_array[i])
            #print("pay_year =", self.pay_year)
        
        return self.payments

    #general print fxn for all
    def NPVprint(self):
        print("  Vendor NPV:     ", self.NPV["vendor"])
        print("  Utility NPV:    ", self.NPV["utility"])
        print("  AE NPV:         ", self.NPV["AE"])
        print("  Constructor NPV:", self.NPV["constructor"])
        print("  Project NPV:",self.NPV["vendor"]+self.NPV["utility"]+self.NPV["AE"]+self.NPV["constructor"])
        

    def print_npv_timepaths(self, model_name, timepath,output):
        #this prints cumulative discounted NPV by year for each actor in the console
        if not timepath:
            return
        col_w = 14
        sep = "=" * (6 + col_w * len(self.actors))

        print()
        print(sep)
        print(f"  {model_name} — cumulative {output} by year")
        print(sep)

        header = f"{'year':>6}" + "".join(f"{actor:>{col_w}}" for actor in self.actors)
        print(header)
        print("-" * len(header))

        for i, y in enumerate(self.actual_year):
            row = f"{int(y):>6}"
            for actor in self.actors:
                row += f"{timepath[actor][i]:>{col_w},.2f}"
            print(row)
        
        print("-" * len(header))
        final = f"{'final':>6}"
        for actor in self.actors:
            final += f"{timepath[actor][-1]:>{col_w},.2f}"
        print(final)
        print()
    


    """FIXED PRICE"""
    def fixed_price(self):
        self.completion_index(self.full_progress_array)

        def completion_payout_year(actual_progress):
            """
            Map design progress index to payout year. We assume design progress array starts at design year 0 and payout historically
            occurred at year == design_time (i.e., after the design phase finishes). If design actually completes at index i (0-based), we place payout at absolute year = i + 1.
            """
            idx = self.completion_index(actual_progress)
            if idx is None:
                return -1 #BL: you had logic later to use -1 if it went to the last year, so putting it here for conciseness
            # payout year is the year after the progress index (e.g., if index 3 -> payout year 4)
            return idx + 1

        #determine actual payout years from actual progress arrays
        self.build_payout_year = completion_payout_year(self.actual_build_progress)+len(self.actual_design_progress)
        self.build_target_payout_year = completion_payout_year(self.target_build_progress)+len(self.target_design_progress)

        #this could be an optional true/false "button" where we can decide if we want to wait to pay out design until after build is complete (wait until build is complete = false)
        self.fp_design_payout_milestone = True
        if self.fp_design_payout_milestone:
            self.design_payout_year = completion_payout_year(self.actual_design_progress)
            self.design_target_payout_year = completion_payout_year(self.target_design_progress)
        else:
            self.design_payout_year = self.build_payout_year
            self.design_target_payout_year = self.build_target_payout_year 
            
        #self.actual_design_time = completion_payout_year(self.actual_design_progress)
        self.actual_build_time = self.build_payout_year - self.actual_design_time

        for actor in self.actors:
            #fixed price (fp) non-discounted revenues — MILESTONE ONLY 
            self.nondisc_costs[actor]= np.zeros_like(self.actual_year, dtype=float)
            self.fp_nondisc_revenue[actor]= np.zeros_like(self.actual_year, dtype=float)

        for actor in self.actors:
            #non-discounted costs
            # DESIGN period
            self.nondisc_costs[actor][self.mask_design] = (self.design_cost / self.actual_design_time) * self.percent_design[actor]
            # BUILD period
            self.nondisc_costs[actor][self.mask_build] = (self.build_cost / self.actual_build_time) * self.percent_build[actor]
            # O&M period starts when revenue starts
            self.nondisc_costs[actor][self.mask_om] = self.OM_per_year * self.percent_OM_to[actor]
            #discounted costs
            self.disc_costs[actor] = np.array(self.nondisc_costs[actor] / ((1 + self.discount_rate) ** self.actual_year))
            #payouts per actor per phase
            self.fp_design_payout_amount[actor] = (np.sum(self.disc_costs[actor][self.mask_design])) * (1 + self.contingency) * (1 + self.profit_margin)*(1 + self.discount_rate)**self.design_payout_year
            self.fp_build_payout_amount[actor] = (np.sum(self.disc_costs[actor][self.mask_build])) * (1 + self.contingency) * (1 + self.profit_margin)*(1 + self.discount_rate)**self.build_payout_year
            
            self.fp_nondisc_revenue[actor][self.design_payout_year] += self.fp_design_payout_amount[actor]
            self.fp_nondisc_revenue[actor][self.build_payout_year] += self.fp_build_payout_amount[actor]
            
            # i think logic here makes sense -> not double counting bc removing what utility has to pay to others AND making sure utility doesn't subtract it's payout from itself
            #if actor != "utility":
            self.fp_nondisc_revenue["utility"][self.design_payout_year] -= self.fp_design_payout_amount[actor]
            self.fp_nondisc_revenue["utility"][self.build_payout_year] -= self.fp_build_payout_amount[actor]
            
            #utility rev: only begins after build completion + commissioning
            if self.build_payout_year is not None:
                revenue_start_actual = self.build_payout_year + self.commission_time
                if revenue_start_actual < len(self.actual_year):
                    self.fp_nondisc_revenue[actor][self.actual_year >= revenue_start_actual] = self.revenue_per_year * self.percent_revenue_to[actor]
                else:
                    # if revenue start beyond timeline, no revenue is recorded
                    pass
                
        for actor in self.actors:
            #fixed price discounted revenues
            self.fp_disc_revenue[actor] = self.fp_nondisc_revenue[actor] / ((1 + self.discount_rate) ** self.actual_year)
            #net disc flows
            self.net_disc[actor] = -self.disc_costs[actor] + self.fp_disc_revenue[actor]
            #npv cumulative sums (NPV at each year)
            self.NPV_timepath[actor] = np.cumsum(self.net_disc[actor])
            #cumulative costs
            self.cost_timepath[actor] = np.cumsum(self.disc_costs[actor])
            #cumulative revenues
            self.revenue_timepath[actor] = np.cumsum(self.fp_disc_revenue[actor])
            
            # total NPV (end of timeline)
            self.NPV[actor] = float(self.NPV_timepath[actor][-1])

        #print("Design payout year (computed):", self.design_payout_year)
        #print("Build payout year (computed):", self.build_payout_year)
        #print("Fixed Price revenue starts (utility) at year:", (self.build_payout_year + self.commission_time) if self.build_payout_year is not None else None)
        
        self.NPVprint()
        self.print_npv_timepaths("Fixed price",self.NPV_timepath,"NPV")
        self.print_npv_timepaths("Fixed price",self.cost_timepath,"Costs")
        self.print_npv_timepaths("Fixed price",self.revenue_timepath,"Revenue")




    """COST+"""
    def cost_plus(self):
        #self.completion_index(self.full_progress_array)

        self.build_completion_payout_year(self.actual_build_progress, self.actual_design_time, self.actual_build_time)

        #partial progress costs and revenues
        self.design_costs = self.distribute_progress_costs(
        self.actual_design_progress,
        phase_cost=self.design_cost,
        phase_start=0,
        phase_length=self.actual_design_time,
        shares=self.percent_design,
        )
        #print("design costs", self.design_costs)

        self.build_costs = self.distribute_progress_costs(
        self.actual_build_progress,
        phase_cost=self.build_cost,
        phase_start=self.actual_design_time,
        phase_length=self.actual_build_time,
        shares=self.percent_build,
        )
        #print("build costs", self.build_costs)

        self.design_payments = self.distribute_progress_payments(
        self.actual_design_progress,
        phase_cost=self.design_cost,
        phase_start=0,
        phase_length=self.actual_design_time,
        shares=self.percent_design,
        )
        #print("design payments", self.design_payments)

        self.build_payments = self.distribute_progress_payments(
        self.actual_build_progress,
        phase_cost=self.build_cost,
        phase_start=self.actual_design_time,
        phase_length=self.actual_build_time,
        shares=self.percent_build,
        )
        #print("build payments", self.build_payments)

        # Utility may get revenue share from build/design payments if configured (here percent_design_utility = 0)
        #remove?
        """TODO"""
        #self.cp_nondisc_operating_revenue = self.design_payments["utility"] + self.build_payments["utility"]
        #print(self.cp_nondisc_utility_revenue)
        
        #set the costplus markup
        self.markup = (1 + self.profit_margin) #BL: I believe that contingency shouldnt be applied on cost-plus
        
        self.cp_disc_revenue = {actor: np.zeros_like(self.actual_year, dtype=float) for actor in self.actors}

        for actor in self.actors:
            self.om_costs[actor] = np.zeros_like(self.actual_year, dtype=float)
            self.om_costs[actor][self.mask_om] = (self.OM_per_year * self.percent_OM_to[actor])
            
            self.nondisc_costs[actor] = (self.design_costs[actor] + self.build_costs[actor] + self.om_costs[actor])
            
            self.cp_disc_costs[actor] = np.zeros_like(self.actual_year, dtype=float)
            self.cp_disc_costs[actor] = np.array(self.nondisc_costs[actor] / ((1 + self.discount_rate) ** self.actual_year))

        for actor in self.actors:
            if actor == "utility":
                self.cp_nondisc_revenue["utility"] = np.zeros_like(self.actual_year, dtype=float)
                continue

            self.cp_nondisc_revenue[actor] = (self.design_payments[actor] + self.build_payments[actor])

            self.cp_disc_revenue[actor] = np.array(self.cp_nondisc_revenue[actor] / ((1 + self.discount_rate) ** self.actual_year))
            self.cp_disc_revenue[actor] *= self.markup
        

        for actor in self.actors: #need to break this line out, once the arrays have been formed
            if actor == "utility":
                continue

            self.cp_disc_costs["utility"] += self.cp_disc_revenue[actor] #BL: utility has to pay the actor
        
        self.cp_nondisc_operating_revenue = {actor: np.zeros_like(self.actual_year, dtype=float) for actor in self.actors}
        self.cp_disc_operating_revenue = {actor: np.zeros_like(self.actual_year, dtype=float) for actor in self.actors}

        # Utility operational revenue (annual), starts only after build is completed + commissioning
        # Determine actual build completion year mapped to timeline
        #TODO: this doesnt currently configure to let others take a share of the profit. Need to expand to all actors
        self.build_payout_year = self.build_completion_payout_year(self.actual_build_progress, self.actual_design_time, self.actual_build_time)
        if self.build_payout_year is not None:
            self.revenue_start_actual = self.build_payout_year + self.commission_time
            if self.revenue_start_actual < len(self.actual_year):
                """TODO: review"""
                for actor in self.actors:
                    self.cp_nondisc_operating_revenue[actor][self.actual_year >= self.revenue_start_actual] += self.revenue_per_year * self.percent_revenue_to[actor]
                    self.cp_disc_operating_revenue[actor] = self.cp_nondisc_operating_revenue[actor] / ((1 + self.discount_rate) ** self.actual_year)
                    #cp_disc_utility_revenue *= markup #BL: should the markup be applied here?
            else:
                # revenue start beyond timeline => no revenue recorded
                pass
        else:
            # build never completed -> no operational utility revenue
            pass

        for actor in self.actors:
            self.cp_disc_revenue[actor] += self.cp_disc_operating_revenue[actor]

            self.net_disc[actor] = -self.cp_disc_costs[actor] + self.cp_disc_revenue[actor]
            
            #npv cumulative sums (NPV at each year)
            self.NPV_timepath[actor] = np.cumsum(self.net_disc[actor])
            #cumulative costs
            self.cost_timepath[actor] = np.cumsum(self.cp_disc_costs[actor])
            #cumulative revenues
            self.revenue_timepath[actor] = np.cumsum(self.cp_disc_revenue[actor])
            
            # total NPV (end of timeline)
            self.NPV[actor] = float(self.NPV_timepath[actor][-1])

        #print("Cost+ revenue starts (utility) at year:", (self.build_payout_year + self.commission_time) if self.build_payout_year is not None else None)

        self.NPVprint()
        self.print_npv_timepaths("Cost plus",self.NPV_timepath,"NPV")
        self.print_npv_timepaths("Cost plus",self.cost_timepath,"Costs")
        self.print_npv_timepaths("Cost plus",self.revenue_timepath,"Revenue")




    """IPD"""
    def ipd(self):
        self.completion_index(self.full_progress_array) 
        self.build_completion_payout_year(self.actual_build_progress, self.actual_design_time, self.actual_build_time)

        #partial progress costs and revenues
        self.design_costs = self.distribute_progress_costs(
        self.actual_design_progress,
        phase_cost=self.design_cost,
        phase_start=0,
        phase_length=self.actual_design_time,
        shares=self.percent_design,
        )

        self.build_costs = self.distribute_progress_costs(
        self.actual_build_progress,
        phase_cost=self.build_cost,
        phase_start=self.actual_design_time,
        phase_length=self.actual_build_time,
        shares=self.percent_build,
        )

        self.design_payments = self.distribute_progress_payments(
        self.actual_design_progress,
        phase_cost=self.design_cost,
        phase_start=0,
        phase_length=self.actual_design_time,
        shares=self.percent_design,
        )

        self.build_payments = self.distribute_progress_payments(
        self.actual_build_progress,
        phase_cost=self.build_cost,
        phase_start=self.actual_design_time,
        phase_length=self.actual_build_time,
        shares=self.percent_build,
        )

        # Utility may get revenue share from build/design payments if configured (here percent_design_utility = 0)
        self.ipd_nondisc_utility_revenue = self.design_payments["utility"] + self.build_payments["utility"]

        self.markup = (1 + self.profit_margin)
        # Utility operational revenue (annual), starts only after build is completed + commissioning
        # Determine actual build completion year mapped to timeline
        self.build_payout_year = self.build_completion_payout_year(self.actual_build_progress, self.actual_design_time, self.actual_build_time)
        if self.build_payout_year is not None:
            self.revenue_start_actual = self.build_payout_year + self.commission_time
            if self.revenue_start_actual < len(self.actual_year):
                self.ipd_nondisc_utility_revenue[self.actual_year >= self.revenue_start_actual] += self.revenue_per_year * self.percent_revenue_to["utility"]
                self.ipd_disc_utility_revenue = self.ipd_nondisc_utility_revenue / ((1 + self.discount_rate) ** self.actual_year)

            else:
                # revenue start beyond timeline => no revenue recorded
                pass
        else:
            # build never completed -> no operational utility revenue
            pass

        #not sure if target cost or actual cost makes more sense -> target seems simpler
        self.target_cost = self.design_cost + self.build_cost
        self.fp_target_price = (self.target_cost) * (1 + self.contingency) * (1 + self.profit_margin)
        self.cp_target_price = self.target_cost * (1 + self.profit_margin)
        #could make this into an input later?
        self.ipd_margin = 0.05 #thinking this is what will make ipd a little offset from the fp line
        self.ipd_target_price = self.fp_target_price * (1 - self.ipd_margin)

        self.crossover_cost = (self.ipd_target_price / (1 + self.profit_margin)) #does this seem right?

        #could also make this an input later? 0.5 is just bc between fp = 0 and cp = 1
        self.ipd_slope = 0.5

        #maybe an actual cost instead of target here? 
        #TODO: how to calculate this best?
        if self.target_cost <= self.crossover_cost:
            self.ipd_price = self.ipd_target_price
        else:
            self.ipd_price = self.ipd_target_price + (self.ipd_slope * max(0, self.target_cost - self.crossover_cost))

        self.ipd_scaler = self.ipd_target_price / self.cp_target_price
        
        #i think this should be if actual cost > crossover point
        for actor in self.actors:
            self.ipd_nondisc_revenue[actor] = self.cp_nondisc_revenue[actor] * self.ipd_scaler
            self.ipd_disc_revenue[actor] = np.zeros_like(self.actual_year, dtype=float)
            self.ipd_disc_revenue[actor] = self.ipd_nondisc_revenue[actor] / ((1 + self.discount_rate) ** self.actual_year)
            self.ipd_disc_revenue[actor] *= self.markup

        for actor in self.actors:
            self.om_costs = np.zeros_like(self.actual_year, dtype=float)
            self.om_costs[self.mask_om] = (self.OM_per_year * self.percent_OM_to[actor])
            
            self.nondisc_costs[actor] = (self.design_costs[actor] + self.build_costs[actor] + self.om_costs)
            #self.ipd_nondisc_revenue[actor] = (self.design_payments[actor] + self.build_payments[actor])
            
            self.ipd_disc_costs[actor] = np.zeros_like(self.actual_year, dtype=float)
            self.ipd_disc_costs[actor] = np.array(self.nondisc_costs[actor] / ((1 + self.discount_rate) ** self.actual_year))

            #self.ipd_disc_revenue[actor] = np.zeros_like(self.actual_year, dtype=float)
            #self.ipd_disc_revenue[actor] = np.array(self.ipd_nondisc_revenue[actor] / ((1 + self.discount_rate) ** self.actual_year))
            #self.ipd_disc_revenue[actor] *= self.markup

        for actor in self.actors: #need to break this line out, once the arrays have been formed
            if actor == "utility":
                continue
            
            self.ipd_disc_costs["utility"] += self.ipd_disc_revenue[actor]
        
        for actor in self.actors:
            self.net_disc[actor] = -self.ipd_disc_costs[actor] + self.ipd_disc_revenue[actor]
            
            if actor == "utility":
                self.net_disc[actor] += self.ipd_disc_utility_revenue

            #npv cumulative sums (NPV at each year)
            self.NPV_timepath[actor] = np.cumsum(self.net_disc[actor])
            #cumulative costs
            self.cost_timepath[actor] = np.cumsum(self.ipd_disc_costs[actor])
            #cumulative revenues
            self.revenue_timepath[actor] = np.cumsum(self.ipd_disc_revenue[actor])
            
            # total NPV (end of timeline)
            self.NPV[actor] = float(self.NPV_timepath[actor][-1])

        #print("IPD Utility NPV:    ", self.NPV["utility"])
        #print("IPD total project NPV:", self.NPV)
        
        #print("IPD revenue starts (utility) at year:", (self.build_payout_year + self.commission_time) if self.build_payout_year is not None else None)

        #self.NPVprint()
        #self.print_npv_timepaths("IPD",self.NPV_timepath,"NPV")
        #self.print_npv_timepaths("IPD",self.cost_timepath,"Costs")
        #self.print_npv_timepaths("IPD",self.revenue_timepath,"Revenue")