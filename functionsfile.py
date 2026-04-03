# -*- coding: utf-8 -*-
"""
BL TODOs:
    - At the moment build_cost is not variable (needs target and actual)
"""

import numpy as np


"""work this into the inputs file as a target and actual progress arrays
target_design_progress=np.zeros(design_time)
target_design_progress[1]=50
target_design_progress[2]=75
target_design_progress[3]=100
target_build_progress=np.zeros(design_time + build_time)
target_build_progress[-1]=100
actual_design_progress=np.zeros(actual_design_time)
actual_design_progress[1]=50
actual_design_progress[2]=75
actual_design_progress[3]=100
actual_build_progress=np.zeros(actual_design_time + actual_build_time)
#actual_build_progress[-2]=50
actual_build_progress[-1]=100
"""

class PDSystems:

    """for ALL functions"""
    def _init_(operating_time,design_time,build_time,commission_time): #TODO: ensure all input variables here
        #TODO: any variable you want to be visible to all functions should have self. at the start.
        self.year = np.arange(0, operating_time + design_time + build_time + commission_time)
        self.target_progress = np.append(target_design_progress, target_build_progress)
        self.actual_progress = np.append(actual_design_progress, actual_build_progress)

        self.progress_array = np.zeros_like(year)
        start_index = 0
        self.end_index = start_index + actual_progress.shape[0]
        self.progress_array[start_index:end_index] = actual_progress

        #Setup masks
        mask_design = year < actual_design_time
        mask_build = (year >= actual_design_time) & (year < actual_design_time + actual_build_time)
        mask_om = year >= (actual_design_time + actual_build_time)

        #Dictionaries for payouts
        self.nondisc_costs = {}
        self.disc_costs = {}
        self.net_disc={}

        self.fp_nondisc_revenue={}
        self.fp_design_payout_amount={}
        self.fp_build_payout_amount={}

        self.cp_disc_costs={}
        self.cp_nondisc_revenue={}

        self.ipd_disc_costs={}
        self.ipd_nondisc_revenue={}

        self.fp_disc_revenue={}
        self.cp_disc_revenue={}
        self.ipd_disc_revenue={}

        self.NPV_timepath={}
        self.NPV={}


    def completion_index(self,progress_array): 
        """Return the first index where progress >= 100; else return None."""
        idx = np.where(progress_array >= 100)[0]
        return int(idx[0]) if idx.size > 0 else None

    def map_sample_to_phase_year(self,i, n_years, phase_start, phase_length):
        """Map a sample index i (0-based) from a progress array of length n_years into a year within the phase: an integer in [phase_start, phase_start + phase_length - 1].
        We map the sample's completion (i+1)/n_samples fraction of the phase to a year with: year_within = ceil((i+1) / n_samples * phase_length) - 1
        This assigns early samples to earlier years and the last sample to the last phase year."""
        if n_years <= 0:
            raise ValueError("n_years must be > 0")
        frac = (i + 1) / n_years
        year_within = int(np.ceil(frac * phase_length)) - 1
        year_within = max(0, min(phase_length - 1, year_within))
        return phase_start + year_within

    def build_completion_payout_year(self,actual_build_progress, design_time, build_time):
        """Return the absolute year when build progress reaches 100% (map sample index to a year).
        If build never reaches 100%, return None."""
        idx = completion_index(actual_build_progress)
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
    def NPVprint(NPV):
        print("  Vendor NPV:     ", NPV["vendor"])
        print("  Utility NPV:    ", NPV["utility"])
        print("  AE NPV:         ", NPV["AE"])
        print("  Constructor NPV:", NPV["constructor"])



    """FIXED PRICE"""
    def fixed_price(self):
        completion_index(progress_array)

        def completion_payout_year(actual_progress):
            """
            Map design progress index to payout year.
            We assume design progress array starts at design year 0 and payout historically
            occurred at year == design_time (i.e., after the design phase finishes).
            If design actually completes at index i (0-based), we place payout at absolute year = i + 1.
            """
            idx = completion_index(actual_progress)
            if idx is None:
                return -1 #BL: you had logic later to use -1 if it went to the last year, so putting it here for conciseness
            # payout year is the year after the progress index (e.g., if index 3 -> payout year 4)
            return idx + 1

        #determine actual payout years from actual progress arrays
        self.build_payout_year = completion_payout_year(actual_build_progress)
        self.build_target_payout_year = completion_payout_year(target_build_progress)

        if fp_design_payout_milestone:
            self.design_payout_year = completion_payout_year(actual_design_progress)
            self.design_target_payout_year = completion_payout_year(target_design_progress)
        else:
            self.design_payout_year = build_payout_year
            self.design_target_payout_year = build_target_payout_year 

        self.actual_design_time = completion_payout_year(actual_design_progress)
        self.actual_build_time = build_payout_year - actual_design_time


        for actor in actors:
                    #fixed price (fp) non-discounted revenues — MILESTONE ONLY 
            nondisc_costs[actor]= np.zeros_like(year, dtype=float)
            fp_nondisc_revenue[actor]= np.zeros_like(year, dtype=float)

        for actor in actors:
            #non-discounted costs
            # DESIGN period
            nondisc_costs[actor][mask_design] = (design_cost / actual_design_time) * percent_design[actor]
            # BUILD period
            nondisc_costs[actor][mask_build] = (build_cost / actual_build_time) * percent_build[actor]
            # O&M period starts when revenue starts
            nondisc_costs[actor][mask_om] = OM_per_year * percent_OM_to[actor]
            #discounted costs
            disc_costs[actor] = np.array(nondisc_costs[actor] / ((1 + discount_rate) ** year))

            fp_design_payout_amount[actor] = (np.sum(disc_costs[actor][mask_design])) * (1 + contingency) * (1 + profit_margin)*(1 + discount_rate)**design_target_payout_year
            fp_build_payout_amount[actor] = (np.sum(disc_costs[actor][mask_build])) * (1 + contingency) * (1 + profit_margin)*(1 + discount_rate)**build_target_payout_year
            
            fp_nondisc_revenue[actor][design_payout_year] += fp_design_payout_amount[actor]
            fp_nondisc_revenue[actor][build_payout_year] += fp_build_payout_amount[actor]
            fp_nondisc_revenue["utility"][design_payout_year] -= fp_design_payout_amount[actor]
            fp_nondisc_revenue["utility"][build_payout_year] -= fp_build_payout_amount[actor]
            
            #utility rev: only begins after build completion + commissioning
            if build_payout_year is not None:
                revenue_start_actual = build_payout_year + commission_time
                if revenue_start_actual < len(year):
                    fp_nondisc_revenue[actor][year >= revenue_start_actual] = revenue_per_year * percent_revenue_to[actor]
                else:
                    # if revenue start beyond timeline, no revenue is recorded
                    pass
                
        for actor in actors:
            #fixed price discounted revenues
            fp_disc_revenue[actor] = fp_nondisc_revenue[actor] / ((1 + discount_rate) ** year)
            #net disc flows
            net_disc[actor] = -disc_costs[actor] + fp_disc_revenue[actor]
            #npv cumulative sums (NPV at each year)
            NPV_timepath[actor] = np.cumsum(net_disc[actor])
            # total NPV (end of timeline)
            NPV[actor] = float(NPV_timepath[actor][-1])


        print("Design payout year (computed):", design_payout_year)
        print("Build payout year (computed):", build_payout_year)
        print("Revenue starts (utility) at year:", (build_payout_year + commission_time) if build_payout_year is not None else None)
        NPVprint()

    """
        # If you want the year-by-year arrays for plotting/export:
        results = {
            "year": year,
            "nondisc_costs":nondisc_costs,
            "fp_nondisc_revenue": fp_nondisc_revenue,
            "net_disc": net_disc,
            "NPV_timepath": NPV_timepath,
        }
        #print(results)
    """




    """COST+"""
    def cost_plus(self):
        completion_index(progress_array)

        #map_sample_to_phase_year(i, n_years, phase_start, phase_length)

        def distribute_progress_costs(progress_array, phase_cost, phase_start, phase_length, shares):
            """Convert a cumulative progress array (percent 0..100) into an annual payment array for each party in shares (dict with keys e.g. 'vendor','AE','constructor','utility').
            Returns dict of arrays (same length as 'year' timeline). Payment for each party = delta_progress_fraction * phase_cost * party_share.
            delta_progress_fraction = (progress[i] - progress[i-1]) / 100, with progress[-1]=0. Each delta is assigned to the mapped year computed by map_sample_to_phase_year. """
            
            self.n_year = len(progress_array)
            self.costs = {k: np.zeros_like(year, dtype=float) for k in shares.keys()}
            """from ben"""
            self.cum_progress_frac = progress_array / 100.0
            
            delta_cum_progress_frac = [0]
            for j in range(n_year-1):
                delta_cum_progress_frac.append(cum_progress_frac[j+1] - cum_progress_frac[j])
            #print(delta_cum_progress_frac)

            for i in range(n_year):
                # which year to assign this sample's payment to
                self.pay_year = map_sample_to_phase_year(i, n_year, phase_start, phase_length)
                # guard: if pay_year outside timeline, cap to last year
                #if pay_year < 0:
                #    pay_year = 0
                if pay_year >= len(year):
                    continue

                for actor, share in shares.items():
                    self.costs[actor][pay_year] += delta_cum_progress_frac[i] * phase_cost * share
                    #print("CP non disc costs:", actor, pay_year, delta_cum_progress_frac[i] * phase_cost * share)
            return costs

        def distribute_progress_payments(progress_array, phase_cost, phase_start, phase_length, shares):
            """Convert a cumulative progress array (percent 0..100) into an annual payment array for each party in shares (dict with keys e.g. 'vendor','AE','constructor','utility').
            Returns dict of arrays (same length as 'year' timeline). Payment for each party = delta_progress_fraction * phase_cost * party_share.
            delta_progress_fraction = (progress[i] - progress[i-1]) / 100, with progress[-1]=0. Each delta is assigned to the mapped year computed by map_sample_to_phase_year. """
            
            self.n_year = len(progress_array)
            self.payments = {k: np.zeros_like(year, dtype=float) for k in shares.keys()}
            """from ben"""
            self.cum_progress_frac = progress_array / 100.0
            
            delta_cum_progress_frac = [0]
            for j in range(n_year-1):
                delta_cum_progress_frac.append(cum_progress_frac[j+1] - cum_progress_frac[j])
            #print(delta_cum_progress_frac)

            for i in range(n_year):
                # which year to assign this sample's payment to
                self.pay_year = map_sample_to_phase_year(i, n_year, phase_start, phase_length)
                # guard: if pay_year outside timeline, cap to last year
                #if pay_year < 0:
                #    pay_year = 0
                if pay_year >= len(year):
                    continue

                for actor, share in shares.items():
                    self.payments[actor][pay_year] += delta_cum_progress_frac[i] * phase_cost * share
                    #print("CP non disc payments:", actor, pay_year, delta_cum_progress_frac[i] * phase_cost * share)
            return payments

        build_completion_payout_year(actual_build_progress, design_time, build_time)

        #partial progress costs and revenues
        self.design_costs = distribute_progress_costs(
        actual_design_progress,
        phase_cost=design_cost,
        phase_start=0,
        phase_length=design_time,
        shares=percent_design,
        )

        self.build_costs = distribute_progress_costs(
        actual_build_progress,
        phase_cost=build_cost,
        phase_start=design_time,
        phase_length=build_time,
        shares=percent_build,
        )

        self.design_payments = distribute_progress_payments(
        actual_design_progress,
        phase_cost=design_cost,
        phase_start=0,
        phase_length=design_time,
        shares=percent_design,
        )

        self.build_payments = distribute_progress_payments(
        actual_build_progress,
        phase_cost=build_cost,
        phase_start=design_time,
        phase_length=build_time,
        shares=percent_build,
        )

        # Utility may get revenue share from build/design payments if configured (here percent_design_utility = 0)
        self.cp_nondisc_utility_revenue = design_payments["utility"] + build_payments["utility"]
        
        #set the costplus markup
        self.markup = (1 + contingency) * (1 + profit_margin) #BL: I believe that contingency shouldnt be applied on cost-plus
        
        # Utility operational revenue (annual), starts only after build is completed + commissioning
        # Determine actual build completion year mapped to timeline
        self.build_payout_year = build_completion_payout_year(actual_build_progress, design_time, build_time)
        if build_payout_year is not None:
            self.revenue_start_actual = build_payout_year + commission_time
            if revenue_start_actual < len(year):
                cp_nondisc_utility_revenue[year >= revenue_start_actual] += revenue_per_year * percent_revenue_to["utility"]
                self.cp_disc_utility_revenue = cp_nondisc_utility_revenue / ((1 + discount_rate) ** year)
                
                #cp_disc_utility_revenue *= markup #BL: should the markup be applied here?
            else:
                # revenue start beyond timeline => no revenue recorded
                pass
        else:
            # build never completed -> no operational utility revenue
            pass
        
        
        for actor in actors:
            nondisc_costs[actor] = (design_costs[actor] + build_costs[actor])
            cp_nondisc_revenue[actor] = (design_payments[actor] + build_payments[actor])
            
            cp_disc_costs[actor] = np.zeros_like(year, dtype=float)
            cp_disc_costs[actor] = np.array(nondisc_costs[actor] / ((1 + discount_rate) ** year))
            #cp_disc_costs[actor] *= markup #BL: markup should only be applied to revenue, not costs

            cp_disc_revenue[actor] = np.zeros_like(year, dtype=float)
            cp_disc_revenue[actor] = np.array(cp_nondisc_revenue[actor] / ((1 + discount_rate) ** year))
            cp_disc_revenue[actor] *= markup
        
        for actor in actors: #need to break this line out, once the arrays have been formed
            cp_disc_costs["utility"] += cp_disc_revenue[actor] #BL: utility has to pay the actor
        
        for actor in actors:
            net_disc[actor] = -cp_disc_costs[actor] + cp_disc_revenue[actor]
            
            #BL: corrected the below line to ensure that the utility is the actor to which this is applied
            if actor == "utility":
                net_disc[actor] += cp_disc_utility_revenue
            
            #npv cumulative sums (NPV at each year)
            self.NPV_timepath[actor] = np.cumsum(net_disc[actor])
            # total NPV (end of timeline)
            self.NPV[actor] = float(NPV_timepath[actor][-1])


        #print("Design_time:", design_time, "Build_time:", build_time)
        #print("Design progress samples:", actual_design_progress)
        #print("Build progress samples:", actual_build_progress)
        #print("Build payout year:", build_payout_year)
        print("Revenue starts (utility) at year:", (build_payout_year + commission_time) if build_payout_year is not None else None)

        NPVprint()



    """IPD"""
    def ipd(self):
        completion_index(progress_array)
         
        def distribute_progress_costs(progress_array, phase_cost, phase_start, phase_length, shares):
          
            self.n_year = len(progress_array)
            self.costs = {k: np.zeros_like(year, dtype=float) for k in shares.keys()}
            self.cum_progress_frac = progress_array / 100.0
            
            delta_cum_progress_frac = [0]
            for j in range(n_year-1):
                delta_cum_progress_frac.append(cum_progress_frac[j+1] - cum_progress_frac[j])

            for i in range(n_year):
                self.pay_year = map_sample_to_phase_year(i, n_year, phase_start, phase_length)
                # guard: if pay_year outside timeline, cap to last year
                #if pay_year < 0:
                #    pay_year = 0
                if pay_year >= len(year):
                    continue
                for actor, share in shares.items():
                    costs[actor][pay_year] += delta_cum_progress_frac[i] * phase_cost * share
            return costs

        def distribute_progress_payments(progress_array, phase_cost, phase_start, phase_length, shares):
            
            self.n_year = len(progress_array)
            self.payments = {k: np.zeros_like(year, dtype=float) for k in shares.keys()}
            self.cum_progress_frac = progress_array / 100.0
            
            delta_cum_progress_frac = [0]
            for j in range(n_year-1):
                delta_cum_progress_frac.append(cum_progress_frac[j+1] - cum_progress_frac[j])
            #print(delta_cum_progress_frac)

            for i in range(n_year):
                # which year to assign this sample's payment to
                self.pay_year = map_sample_to_phase_year(i, n_year, phase_start, phase_length)
                # guard: if pay_year outside timeline, cap to last year
                #if pay_year < 0:
                #    pay_year = 0
                if pay_year >= len(year):
                    continue

                for actor, share in shares.items():
                    payments[actor][pay_year] += delta_cum_progress_frac[i] * phase_cost * share
                    #print("IPD non disc payments:", actor, pay_year, delta_cum_progress_frac[i] * phase_cost * share)
            return payments

        build_completion_payout_year(actual_build_progress, design_time, build_time)

        #partial progress costs and revenues
        self.design_costs = distribute_progress_costs(
        actual_design_progress,
        phase_cost=design_cost,
        phase_start=0,
        phase_length=design_time,
        shares=percent_design,
        )

        self.build_costs = distribute_progress_costs(
        actual_build_progress,
        phase_cost=build_cost,
        phase_start=design_time,
        phase_length=build_time,
        shares=percent_build,
        )

        self.design_payments = distribute_progress_payments(
        actual_design_progress,
        phase_cost=design_cost,
        phase_start=0,
        phase_length=design_time,
        shares=percent_design,
        )

        self.build_payments = distribute_progress_payments(
        actual_build_progress,
        phase_cost=build_cost,
        phase_start=design_time,
        phase_length=build_time,
        shares=percent_build,
        )

        # Utility may get revenue share from build/design payments if configured (here percent_design_utility = 0)
        self.ipd_nondisc_utility_revenue = design_payments["utility"] + build_payments["utility"]

        # Utility operational revenue (annual), starts only after build is completed + commissioning
        # Determine actual build completion year mapped to timeline
        self.build_payout_year = build_completion_payout_year(actual_build_progress, design_time, build_time)
        if build_payout_year is not None:
            self.revenue_start_actual = build_payout_year + commission_time
            if revenue_start_actual < len(year):
                ipd_nondisc_utility_revenue[year >= revenue_start_actual] += revenue_per_year * percent_revenue_to["utility"]
                self.ipd_disc_utility_revenue = ipd_nondisc_utility_revenue / ((1 + discount_rate) ** year)
                self.markup = (1 + contingency) * (1 + profit_margin)
                ipd_disc_utility_revenue *= markup
            else:
                # revenue start beyond timeline => no revenue recorded
                pass
        else:
            # build never completed -> no operational utility revenue
            pass

        for actor in actors:
            nondisc_costs[actor] = (design_costs[actor] + build_costs[actor])
            ipd_nondisc_revenue[actor] = (design_payments[actor] + build_payments[actor])
            
            ipd_disc_costs[actor] = np.zeros_like(year, dtype=float)
            ipd_disc_costs[actor] = np.array(nondisc_costs[actor] / ((1 + discount_rate) ** year))
            ipd_disc_costs[actor] *= markup

            ipd_disc_revenue[actor] = np.zeros_like(year, dtype=float)
            ipd_disc_revenue[actor] = np.array(ipd_nondisc_revenue[actor] / ((1 + discount_rate) ** year))
            ipd_disc_revenue[actor] *= markup

            net_disc[actor] = -ipd_disc_costs[actor] + ipd_disc_revenue[actor]
            net_disc["utility"] = -ipd_disc_costs[actor] + ipd_disc_revenue[actor] + ipd_disc_utility_revenue
            #npv cumulative sums (NPV at each year)
            self.NPV_timepath[actor] = np.cumsum(net_disc[actor])
            # total NPV (end of timeline)
            self.NPV[actor] = float(NPV_timepath[actor][-1])


        #print("Design_time:", design_time, "Build_time:", build_time)
        #print("Design progress samples:", actual_design_progress)
        #print("Build progress samples:", actual_build_progress)
        #print("Build payout year:", build_payout_year)
        print("Revenue starts (utility) at year:", (build_payout_year + commission_time) if build_payout_year is not None else None)

        NPVprint()
