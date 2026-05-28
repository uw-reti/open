# -*- coding: utf-8 -*-
"""
BL TODOs:
    - At the moment build_cost is not variable (needs target and actual)
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

        self.percent_design = inputs["design_shares"]
        self.percent_build = inputs["build_shares"]
        self.percent_OM_to = inputs["om_shares"]
        self.percent_revenue_to = inputs["revenue_shares"]

        self.actors = ["vendor", "AE", "constructor", "utility"]


        self.year = np.arange(0, self.operating_time + self.design_time + self.build_time + self.commission_time)
        self.target_progress = np.append(self.target_design_progress, self.target_build_progress)
        self.actual_progress = np.append(self.actual_design_progress, self.actual_build_progress)

        self.progress_array = np.zeros_like(self.year)
        end_index = len(self.actual_progress)
        self.progress_array[:end_index] = self.actual_progress
        """start_index = 0
        end_index = start_index + actual_progress.shape[0]
        progress_array[start_index:end_index] = actual_progress"""

        #Setup masks
        self.actual_design_time = len(self.actual_design_progress)
        self.actual_build_time = len(self.actual_build_progress)

        self.mask_design = self.year < self.actual_design_time
        self.mask_build = (
            (self.year >= self.actual_design_time)
            & (self.year < self.actual_design_time + self.actual_build_time)
        )
        self.mask_om = self.year >= (self.actual_design_time + self.actual_build_time)
        #mask_design = year < actual_design_time
        #mask_build = (year >= actual_design_time) & (year < actual_design_time + actual_build_time)
        #mask_om = year >= (actual_design_time + actual_build_time)

        #Dictionaries for payouts
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

        self.ipd_disc_costs = {}
        self.ipd_nondisc_revenue = {}
        self.ipd_disc_revenue = {}

        self.NPV_timepath = {}
        self.cost_timepath = {}
        self.revenue_timepath = {}
        self.NPV = {}


    #fxn that returns the first index where progress >= 100; else return None
    def completion_index(self,progress_array):
        idx = np.where(progress_array >= 100)[0]
        return int(idx[0]) if idx.size > 0 else None

    
    #fxn that maps a sample index i (0-based) from a progress array of length n_years into a year within the phase: an integer in [phase_start, phase_start + phase_length - 1]
    def map_sample_to_phase_year(self,i, n_years, phase_start, phase_length):
        if n_years <= 0:
            raise ValueError("n_years must be > 0")
        frac = (i + 1) / n_years
        year_within = int(np.ceil(frac * phase_length)) - 1
        year_within = max(0, min(phase_length - 1, year_within))
        return int(phase_start + year_within)

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
    def build_completion_payout_year(self,actual_build_progress, design_time, build_time):
        idx = self.completion_index(actual_build_progress)
        if idx is None:
            return None
        
        n_years = len(actual_build_progress)
        # position fraction within build
        frac = (idx + 1) / n_years
        year_within = int(np.ceil(frac * build_time))  # 1..build_time
        year_within = max(1, min(build_time, year_within))
        payout_year = design_time + year_within
        return payout_year

    #general print fxn for all
    def NPVprint(self):
        print("  Vendor NPV:     ", self.NPV["vendor"])
        print("  Utility NPV:    ", self.NPV["utility"])
        print("  AE NPV:         ", self.NPV["AE"])
        print("  Constructor NPV:", self.NPV["constructor"])
        

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

        for i, y in enumerate(self.year):
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
        self.completion_index(self.progress_array)

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
            
        self.actual_design_time = completion_payout_year(self.actual_design_progress)
        self.actual_build_time = self.build_payout_year - self.actual_design_time

        for actor in self.actors:
            #fixed price (fp) non-discounted revenues — MILESTONE ONLY 
            self.nondisc_costs[actor]= np.zeros_like(self.year, dtype=float)
            self.fp_nondisc_revenue[actor]= np.zeros_like(self.year, dtype=float)

        for actor in self.actors:
            #non-discounted costs
            # DESIGN period
            self.nondisc_costs[actor][self.mask_design] = (self.design_cost / self.actual_design_time) * self.percent_design[actor]
            # BUILD period
            self.nondisc_costs[actor][self.mask_build] = (self.build_cost / self.actual_build_time) * self.percent_build[actor]
            # O&M period starts when revenue starts
            self.nondisc_costs[actor][self.mask_om] = self.OM_per_year * self.percent_OM_to[actor]
            #discounted costs
            self.disc_costs[actor] = np.array(self.nondisc_costs[actor] / ((1 + self.discount_rate) ** self.year))
            #payouts per actor per phase
            self.fp_design_payout_amount[actor] = (np.sum(self.disc_costs[actor][self.mask_design])) * (1 + self.contingency) * (1 + self.profit_margin)*(1 + self.discount_rate)**self.design_target_payout_year
            self.fp_build_payout_amount[actor] = (np.sum(self.disc_costs[actor][self.mask_build])) * (1 + self.contingency) * (1 + self.profit_margin)*(1 + self.discount_rate)**self.build_target_payout_year
            
            #----should I be separating the nondisc revenues into one for each phase or does this logic make sense? and maybe this is double counting utility?
            self.fp_nondisc_revenue[actor][self.design_payout_year] += self.fp_design_payout_amount[actor]
            self.fp_nondisc_revenue[actor][self.build_payout_year] += self.fp_build_payout_amount[actor]
            #----is this why final values aren't adding up? is there a way to pass through just the other 3 actors and not utility?
            self.fp_nondisc_revenue["utility"][self.design_payout_year] -= self.fp_design_payout_amount[actor]
            self.fp_nondisc_revenue["utility"][self.build_payout_year] -= self.fp_build_payout_amount[actor]
            
            #utility rev: only begins after build completion + commissioning
            if self.build_payout_year is not None:
                revenue_start_actual = self.build_payout_year + self.commission_time
                if revenue_start_actual < len(self.year):
                    self.fp_nondisc_revenue[actor][self.year >= revenue_start_actual] = self.revenue_per_year * self.percent_revenue_to[actor]
                else:
                    # if revenue start beyond timeline, no revenue is recorded
                    pass
                
        for actor in self.actors:
            #fixed price discounted revenues
            self.fp_disc_revenue[actor] = self.fp_nondisc_revenue[actor] / ((1 + self.discount_rate) ** self.year)
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

        print("Design payout year (computed):", self.design_payout_year)
        print("Build payout year (computed):", self.build_payout_year)
        print("Revenue starts (utility) at year:", (self.build_payout_year + self.commission_time) if self.build_payout_year is not None else None)
        self.NPVprint()
        self.print_npv_timepaths("Fixed price",self.NPV_timepath,"NPV")
        self.print_npv_timepaths("Fixed price",self.cost_timepath,"Costs")
        self.print_npv_timepaths("Fixed price",self.revenue_timepath,"Revenue")


    """COST+"""
    def cost_plus(self):
        self.completion_index(self.progress_array)

        #map_sample_to_phase_year(i, n_years, phase_start, phase_length)

        def distribute_progress_costs(progress_array, phase_cost, phase_start, phase_length, shares):
            """Convert a cumulative progress array (percent 0..100) into an annual payment array for each party in shares (dict with keys e.g. 'vendor','AE','constructor','utility').
            Returns dict of arrays (same length as 'year' timeline). Payment for each party = delta_progress_fraction * phase_cost * party_share.
            delta_progress_fraction = (progress[i] - progress[i-1]) / 100, with progress[-1]=0. Each delta is assigned to the mapped year computed by map_sample_to_phase_year. """
            
            self.n_year = len(progress_array)
            self.costs = {k: np.zeros_like(self.year, dtype=float) for k in shares.keys()}
            """from ben"""
            self.cum_progress_frac = progress_array / 100.0
            
            #does this need to be self.?
            delta_cum_progress_frac = np.concatenate(([self.cum_progress_frac[0]], np.diff(self.cum_progress_frac)))

            for i in range(self.n_year):
                # which year to assign this sample's payment to
                self.pay_year = self.map_sample_to_phase_year(i, self.n_year, phase_start, phase_length)
                # guard: if pay_year outside timeline, cap to last year
                #if pay_year < 0:
                #    pay_year = 0
                if self.pay_year >= len(self.year):
                    continue

                for actor, share in shares.items():
                    self.costs[actor][self.pay_year] += delta_cum_progress_frac[i] * phase_cost * share
                    #print("CP non disc costs:", actor, pay_year, delta_cum_progress_frac[i] * phase_cost * share)
            return self.costs

        def distribute_progress_payments(progress_array, phase_cost, phase_start, phase_length, shares):
            """Convert a cumulative progress array (percent 0..100) into an annual payment array for each party in shares (dict with keys e.g. 'vendor','AE','constructor','utility').
            Returns dict of arrays (same length as 'year' timeline). Payment for each party = delta_progress_fraction * phase_cost * party_share.
            delta_progress_fraction = (progress[i] - progress[i-1]) / 100. Each increment is booked to the phase year when cumulative progress reaches progress[i]
            (map_cumulative_progress_to_phase_year), so delayed/back-loaded curves move cash later vs index-only mapping."""
            
            self.n_year = len(progress_array)
            self.payments = {k: np.zeros_like(self.year, dtype=float) for k in shares.keys()}
            """from ben"""
            self.cum_progress_frac = progress_array / 100.0
            
            delta_cum_progress_frac = np.concatenate(([self.cum_progress_frac[0]], np.diff(self.cum_progress_frac)))

            for i in range(self.n_year):
                # Pay this increment when cumulative actual progress reaches progress_array[i] (not by sample index alone).
                self.pay_year = self.map_cumulative_progress_to_phase_year(
                    progress_array[i], phase_start, phase_length
                )
                # guard: if pay_year outside timeline, cap to last year
                #if pay_year < 0:
                #    pay_year = 0
                if self.pay_year >= len(self.year):
                    continue

                for actor, share in shares.items():
                    self.payments[actor][self.pay_year] += delta_cum_progress_frac[i] * phase_cost * share
                    #print("CP non disc payments:", actor, pay_year, delta_cum_progress_frac[i] * phase_cost * share)
            return self.payments

        self.build_completion_payout_year(self.actual_build_progress, self.design_time, self.build_time)

        #partial progress costs and revenues
        self.design_costs = distribute_progress_costs(
        self.actual_design_progress,
        phase_cost=self.design_cost,
        phase_start=0,
        phase_length=self.design_time,
        shares=self.percent_design,
        )

        self.build_costs = distribute_progress_costs(
        self.actual_build_progress,
        phase_cost=self.build_cost,
        phase_start=self.design_time,
        phase_length=self.build_time,
        shares=self.percent_build,
        )

        self.design_payments = distribute_progress_payments(
        self.actual_design_progress,
        phase_cost=self.design_cost,
        phase_start=0,
        phase_length=self.design_time,
        shares=self.percent_design,
        )

        self.build_payments = distribute_progress_payments(
        self.actual_build_progress,
        phase_cost=self.build_cost,
        phase_start=self.design_time,
        phase_length=self.build_time,
        shares=self.percent_build,
        )

        # Utility may get revenue share from build/design payments if configured (here percent_design_utility = 0)
        self.cp_nondisc_utility_revenue = self.design_payments["utility"] + self.build_payments["utility"]
        
        #set the costplus markup
        self.markup = (1 + self.profit_margin) #BL: I believe that contingency shouldnt be applied on cost-plus
        
        # Utility operational revenue (annual), starts only after build is completed + commissioning
        # Determine actual build completion year mapped to timeline
        #TODO: this doesnt currently configure to let others take a share of the profit. Need to expand to all actors
        self.build_payout_year = self.build_completion_payout_year(self.actual_build_progress, self.design_time, self.build_time)
        if self.build_payout_year is not None:
            self.revenue_start_actual = self.build_payout_year + self.commission_time
            if self.revenue_start_actual < len(self.year):
                self.cp_nondisc_utility_revenue[self.year >= self.revenue_start_actual] += self.revenue_per_year * self.percent_revenue_to["utility"]
                self.cp_disc_utility_revenue = self.cp_nondisc_utility_revenue / ((1 + self.discount_rate) ** self.year)
                
                #cp_disc_utility_revenue *= markup #BL: should the markup be applied here?
            else:
                # revenue start beyond timeline => no revenue recorded
                pass
        else:
            # build never completed -> no operational utility revenue
            pass
        
        
        for actor in self.actors:
            self.nondisc_costs[actor] = (self.design_costs[actor] + self.build_costs[actor])
            self.cp_nondisc_revenue[actor] = (self.design_payments[actor] + self.build_payments[actor])
            
            self.cp_disc_costs[actor] = np.zeros_like(self.year, dtype=float)
            self.cp_disc_costs[actor] = np.array(self.nondisc_costs[actor] / ((1 + self.discount_rate) ** self.year))
            #cp_disc_costs[actor] *= markup #BL: markup should only be applied to revenue, not costs

            self.cp_disc_revenue[actor] = np.zeros_like(self.year, dtype=float)
            self.cp_disc_revenue[actor] = np.array(self.cp_nondisc_revenue[actor] / ((1 + self.discount_rate) ** self.year))
            self.cp_disc_revenue[actor] *= self.markup
        
        for actor in self.actors: #need to break this line out, once the arrays have been formed
            self.cp_disc_costs["utility"] += self.cp_disc_revenue[actor] #BL: utility has to pay the actor
        
        for actor in self.actors:
            self.net_disc[actor] = -self.cp_disc_costs[actor] + self.cp_disc_revenue[actor]
            
            #BL: corrected the below line to ensure that the utility is the actor to which this is applied
            if actor == "utility":
                self.net_disc[actor] += self.cp_disc_utility_revenue
            
            #npv cumulative sums (NPV at each year)
            self.NPV_timepath[actor] = np.cumsum(self.net_disc[actor])
            #cumulative costs
            self.cost_timepath[actor] = np.cumsum(self.cp_disc_costs[actor])
            #cumulative revenues
            self.revenue_timepath[actor] = np.cumsum(self.cp_disc_revenue[actor])
            
            # total NPV (end of timeline)
            self.NPV[actor] = float(self.NPV_timepath[actor][-1])


        #print("Design_time:", design_time, "Build_time:", build_time)
        #print("Design progress samples:", actual_design_progress)
        #print("Build progress samples:", actual_build_progress)
        #print("Build payout year:", build_payout_year)
        print("Revenue starts (utility) at year:", (self.build_payout_year + self.commission_time) if self.build_payout_year is not None else None)

        self.NPVprint()
        self.print_npv_timepaths("Cost plus",self.NPV_timepath,"NPV")
        self.print_npv_timepaths("Cost plus",self.cost_timepath,"Costs")
        self.print_npv_timepaths("Cost plus",self.revenue_timepath,"Revenue")


    """IPD"""
    def ipd(self):
        self.completion_index(self.progress_array)
         
        def distribute_progress_costs(progress_array, phase_cost, phase_start, phase_length, shares):
          
            self.n_year = len(progress_array)
            self.costs = {k: np.zeros_like(self.year, dtype=float) for k in shares.keys()}
            self.cum_progress_frac = progress_array / 100.0
            
            #self.?
            delta_cum_progress_frac = np.concatenate(([self.cum_progress_frac[0]], np.diff(self.cum_progress_frac)))
            
            for i in range(self.n_year):
                self.pay_year = self.map_sample_to_phase_year(i, self.n_year, phase_start, phase_length)
                # guard: if pay_year outside timeline, cap to last year
                #if pay_year < 0:
                #    pay_year = 0
                if self.pay_year >= len(self.year):
                    continue
                for actor, share in shares.items():
                    self.costs[actor][self.pay_year] += delta_cum_progress_frac[i] * phase_cost * share
            return self.costs

        def distribute_progress_payments(progress_array, phase_cost, phase_start, phase_length, shares):
            """Same cumulative-% timing as cost_plus: pay each increment in the phase year implied by progress_array[i]."""
            
            self.n_year = len(progress_array)
            self.payments = {k: np.zeros_like(self.year, dtype=float) for k in shares.keys()}
            self.cum_progress_frac = progress_array / 100.0
            
            delta_cum_progress_frac = np.concatenate(([self.cum_progress_frac[0]], np.diff(self.cum_progress_frac)))
            #print(delta_cum_progress_frac)

            for i in range(self.n_year):
                self.pay_year = self.map_cumulative_progress_to_phase_year(
                    progress_array[i], phase_start, phase_length
                )
                # guard: if pay_year outside timeline, cap to last year
                #if pay_year < 0:
                #    pay_year = 0
                if self.pay_year >= len(self.year):
                    continue

                for actor, share in shares.items():
                    self.payments[actor][self.pay_year] += delta_cum_progress_frac[i] * phase_cost * share
                    #print("IPD non disc payments:", actor, pay_year, delta_cum_progress_frac[i] * phase_cost * share)
            return self.payments

        self.build_completion_payout_year(self.actual_build_progress, self.design_time, self.build_time)

        #partial progress costs and revenues
        self.design_costs = distribute_progress_costs(
        self.actual_design_progress,
        phase_cost=self.design_cost,
        phase_start=0,
        phase_length=self.design_time,
        shares=self.percent_design,
        )

        self.build_costs = distribute_progress_costs(
        self.actual_build_progress,
        phase_cost=self.build_cost,
        phase_start=self.design_time,
        phase_length=self.build_time,
        shares=self.percent_build,
        )

        self.design_payments = distribute_progress_payments(
        self.actual_design_progress,
        phase_cost=self.design_cost,
        phase_start=0,
        phase_length=self.design_time,
        shares=self.percent_design,
        )

        self.build_payments = distribute_progress_payments(
        self.actual_build_progress,
        phase_cost=self.build_cost,
        phase_start=self.design_time,
        phase_length=self.build_time,
        shares=self.percent_build,
        )

        # Utility may get revenue share from build/design payments if configured (here percent_design_utility = 0)
        self.ipd_nondisc_utility_revenue = self.design_payments["utility"] + self.build_payments["utility"]

        self.markup = (1 + self.profit_margin)
        # Utility operational revenue (annual), starts only after build is completed + commissioning
        # Determine actual build completion year mapped to timeline
        self.build_payout_year = self.build_completion_payout_year(self.actual_build_progress, self.design_time, self.build_time)
        if self.build_payout_year is not None:
            self.revenue_start_actual = self.build_payout_year + self.commission_time
            if self.revenue_start_actual < len(self.year):
                self.ipd_nondisc_utility_revenue[self.year >= self.revenue_start_actual] += self.revenue_per_year * self.percent_revenue_to["utility"]
                self.ipd_disc_utility_revenue = self.ipd_nondisc_utility_revenue / ((1 + self.discount_rate) ** self.year)
                
                self.ipd_disc_utility_revenue *= self.markup
            else:
                # revenue start beyond timeline => no revenue recorded
                pass
        else:
            # build never completed -> no operational utility revenue
            pass

        for actor in self.actors:
            self.nondisc_costs[actor] = (self.design_costs[actor] + self.build_costs[actor])
            self.ipd_nondisc_revenue[actor] = (self.design_payments[actor] + self.build_payments[actor])
            
            self.ipd_disc_costs[actor] = np.zeros_like(self.year, dtype=float)
            self.ipd_disc_costs[actor] = np.array(self.nondisc_costs[actor] / ((1 + self.discount_rate) ** self.year))

            self.ipd_disc_revenue[actor] = np.zeros_like(self.year, dtype=float)
            self.ipd_disc_revenue[actor] = np.array(self.ipd_nondisc_revenue[actor] / ((1 + self.discount_rate) ** self.year))
            self.ipd_disc_revenue[actor] *= self.markup

        for actor in self.actors: #need to break this line out, once the arrays have been formed
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

        print("Revenue starts (utility) at year:", (self.build_payout_year + self.commission_time) if self.build_payout_year is not None else None)

        self.NPVprint()
        self.print_npv_timepaths("IPD",self.NPV_timepath,"NPV")
        self.print_npv_timepaths("IPD",self.cost_timepath,"Costs")
        self.print_npv_timepaths("IPD",self.revenue_timepath,"Revenue")