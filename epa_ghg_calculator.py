import logging


class EPAGHGCalculator:
    """a port of GHGCalculator.xls 
    (from https://www3.epa.gov/carbon-footprint-calculator/
    Version downloaded 2020-06-15)
    to be used in SCIARA
    
    NOTES:
    * does NOT contain emissions from flying or indirect emissions from consumption!
    
    USAGE:
    * initialize once upfront
    * for each request, call calculate() once
    """

    def __init__(self):
        # nothing to do so far
        pass

    poundsToKg = 1 / 2.2046
    kgToPounds = 2.2046

    flights_average_km_and_costs = {'short': {'kilometersPerTrip': 0, 'co2PerKilometerInKG': 0.0881},
                                    'medium': {'kilometersPerTrip': 0, 'co2PerKilometerInKG': 0.0881},
                                    'long': {'kilometersPerTrip': 0, 'co2PerKilometerInKG': 0.0881}}

    poundsCO2eq_to_GtC = (1
                          / 3.667  # CO2 to C 
                          / 2204.6  # pounds to metric tons 
                          / 1e9  # tons to gigatons
                          )
    """conversion factor from pounds CO2-equivalents to metric gigatons of carbon (GtC)"""

    # Cell labels and optional defaults used in sheet "Personal GHG Calculator":
    input_labels_defaults = dict(
        peopleInHouseholdF5=("How many people live in your home?", 1),
        # F6 = "What is your zipcode?",  # not yet supported
        primaryHeatingSourceF7=("What is your household's primary heating source? "
                                "Enter 1 for natural gas, 2 for electric heat, 3 for oil, "
                                "4 for propane, 5 for wood, or 6 if you do not heat your house",
                                1),
        vehicle1MilesD15=("Vehicle 1, Miles driven",
                          14000.0 * 58e9 / 82e9 / 1.6),  # very rough avg. value for Germany
        # D17 = "Vehicle 2, Miles driven",  # not yet supported
        # D19 = "Vehicle 3, Miles driven",  # not yet supported
        vehicle1MilesUnitG15=("enter 1 if this represents miles per week or 2 if it's miles per year",
                              2),
        vehicleMaintenanceF29=("Do you perform regular maintenance on your vehicles? "
                               "Enter 1 for yes and 2 for no",
                               1),
        naturalGasF37=("How much natural gas does your household use per month? "
                       "If you enter your monthly consumption in thousand cubic feet, you'll get a more "
                       "accurate estimate."
                       "If you enter dollars, our calculations assume you pay $10.68/thousand cubic feet. "
                       "$23 is about average in the United States for a household of one person.",
                       23
                       ),
        naturalGasUnitH37=("Enter 1 for dollars, 2 for thousand cubic feet, 3 for therms",
                           1),
        electricityF42=("How much electricity does your household use per month? "
                        "If you enter your average kilowatt-hours, you'll get a more accurate estimate. "
                        "If you enter dollars, our calculations assume that you pay 11.9 cents/kWh. "
                        "$44 is about average in the United States for a household of one person.",
                        44
                        ),
        electricityUnitH42=("Enter 1 for dollars, 2 for kilowatt-hours",
                            1),
        greenPowerF45=("Does your household currently purchase green power? "
                       "Green power can often be bought through your local utility or through a green power marketer. "
                       "For a description of green power visit (http://www.epa.gov/greenpower/whatis/index.htm). "
                       "Enter 1 for yes, 2 for no",
                       2),
        greenPowerPercentF49=("If so, what portion in per cent of your household's total purchased "
                              "electricity use is green power? "
                              "Enter 100 if you buy all of your electricity as green power.", 0),
        fuelOilF53=("How much fuel oil does your household use per month? "
                    "Divide your annual fuel oil consumption (in gallons or dollars) by 12 to obtain a monthly average."
                    "If you enter your monthly fuel oil use in gallons, you'll get a more accurate estimate. "
                    "If you enter dollars, our calculations assume that you pay $4.02/gallon. "
                    "$72 is about average in the United States for a household of one person.",
                    72),
        fuelOilUnitH53=("Enter 1 for dollars, 2 for gallons",
                        1),
        propaneF57=("How much propane does your household use per month? "
                    "If you enter your monthly propane use in gallons, you'll get a more accurate estimate. "
                    "If you enter dollars, our calculations assume that you pay $2.47/gallon. "
                    "$37 is about average in the United States for a household of one person.",
                    37),
        propaneUnitH57=("Enter 1 for dollars, 2 for gallons",
                        1),
        recycleAluminumF65=("Do you recycle aluminum and steel cans?"
                            "enter 1 for yes and 2 for no",
                            1),
        recyclePlasticF67=("Do you recycle plastic? "
                           "enter 1 for yes and 2 for no",
                           1),
        recycleGlassF69=("Do you recycle glass? "
                         "enter 1 for yes and 2 for no",
                         1),
        recycleNewspaperF71=("Do you recycle newspaper? "
                             "enter 1 for yes and 2 for no",
                             1),
        recycleMagsF73=("Do you recycle magazines? "
                        "enter 1 for yes and 2 for no",
                        1),
        foodPreferences_vegan2MeatScale=("What are your food preferences?"
                                         "enter a value between 0 (vegan) and 1 (heavy meat eater)",
                                         0.9),

        mobility_airplane_short_flights=("How many short flights do you take per year?"
                                         "enter the number", 0),
        mobility_airplane_medium_flights=("How many medium flights do you take per year?"
                                          "enter the number", 0),
        mobility_airplane_long_flights=("How many long flights do you take per year?"
                                        "enter the number", 0),

    )

    # Data from sheet "EMISSION_FACTORS":
    emission_factor_us_total = 1238.5157
    """eGRID subregion annual CO2 equivalent total output emission rate (lb/MWh)
    according to eGRID 9th edition Version 1.0 Subregion File (Year 2010 Data)"""
    # we're not using US subregions in the MVP

    # Data from sheet "Sheet1":  # TODO: add comments specifying physical units!
    AC_electricity_percent = 0.14
    average_elec_CO2_emissions = 14019.997724
    average_FO_CO2_emissions = 12460
    average_mpg = 21.6
    average_waste_emissions = 692
    boiler_replacement_cost_savings = 78.34
    boiler_replacement_savings_FO = 1056
    boiler_replacement_savings_NG = 728
    BTU_per_1000cf_NG = 1023000
    BTU_per_gallon_FO = 138691.09
    BTU_per_gallon_propane = 91335.94
    BTU_per_kWh = 3412
    CO2_C_ratio = 3.67
    computer_energy_monitor_off = 66.5
    computer_energy_off = 143
    computer_energy_sleep_monitor_off = 31.7
    computer_energy_sleep_off = 70.7
    computer_sleep_savings = 107.1
    conventional_fridge_kWh = 810
    conversion_1000cf_to_therm = 10.23
    conversion_QBtu_to_Btu = 1000000000000000
    conversion_Tg_to_lb = 2204622620
    cost_per_kWh = 0.1188
    cost_per_mile = 0.1964
    dryer_energy = 769
    e_factor = None
    e_factor_value = 1238.516 / 1000  # taken from sheet EMISSION_FACTORS, row US Total, converted from lb/MWh to lb/kWh
    EF_fuel_oil_gallon = 22.61
    EF_fuel_oil_MMBtu = 163.05
    EF_natural_gas = 119.58
    EF_natural_gas_therm = 11.68890913124
    EF_passenger_vehicle = 19.6
    EF_propane = 12.43
    ENERGYSTAR_fridge_kWh = 488
    fridge_replacement_kWh_savings = 322
    fuel_oil_cost = 4.02
    gas_cost_gallon = 3.68
    glass_recycling_avoided_emissions = -25.39
    green_power_premium = 0.02
    heating_percent_electricity = 0.09
    heating_percent_fuel_oil = 0.87
    heating_percent_NG = 0.63
    heating_percent_propane = 0.70
    HH_size = 2.57
    HHV_fuel_oil = 138691.09
    HHV_natural_gas = 1023000
    HHV_propane = 91335.94
    kWh_per_load_laundry = 0.96
    lamp_cost_savings = 4.00
    lamp_kWh_savings = 33
    mag_recycling_avoided_emissions = -27.46
    metal_recycling_avoided_emissions = -89.38
    monthly_elec_consumption = 943
    monthly_FO_consumption = 46
    monthly_NG_Consumption = 5500
    monthly_propane_consumption = 39
    natural_gas_cost_1000CF = 10.68
    natural_gas_cost_therm = 1.04
    newspaper_recycling_avoided_emissions = -113.14
    NG_CO2_annual_emissions = 7892
    nonCO2_vehicle_emissions_ratio = 1.01
    oilFuelRate = 0
    plastic_recycling_avoided_emissions = -35.56
    propane_cost = 2.47
    thermostat_cooling_savings = 0.06
    thermostat_heating_savings = 0.03
    vehicle_efficiency_improvements = 0.04
    window_replacement_cost_savings = 150
    window_replacement_energy_savings = 25210000

    # Cell formulae from sheet "Personal GHG Calculator":

    def K15(self):
        return self.average_mpg

    def J26(self):
        """= IF(vehicle1MilesD15=0,
             0,
             IF(vehicle1MilesUnitG15=1,
                (vehicle1MilesD15*52)/K15*EF_passenger_vehicle*(nonCO2_vehicle_emissions_ratio),
                (vehicle1MilesD15)/K15*EF_passenger_vehicle*(nonCO2_vehicle_emissions_ratio)))
           + ... + IF(D23=0, ...)
           + J29
        """
        res = (
                self.vehicle1MilesD15 * (52 if self.vehicle1MilesUnitG15 == 1 else 1) *
                self.EF_passenger_vehicle * self.nonCO2_vehicle_emissions_ratio / self.K15()
                + self.J29()
        )
        logging.debug("EPAGHGCalculator: J26 = %f" % res)
        return res

    def J29(self):
        """pounds/yr

        = (IF(vehicleMaintenanceF29=2,
             IF(vehicle1MilesUnitG15=1,
                (vehicle1MilesD15*52)/K15*EF_passenger_vehicle*(nonCO2_vehicle_emissions_ratio),
                (vehicle1MilesD15)/K15*EF_passenger_vehicle*(nonCO2_vehicle_emissions_ratio))
             *vehicle_efficiency_improvements
             + ... + IF(G23=1, ...)*vehicle_efficiency_improvements,
             "0"))
        """
        res = (
            self.vehicle1MilesD15 * (
                52 if self.vehicle1MilesUnitG15 == 1 else 1
            ) * self.EF_passenger_vehicle * self.nonCO2_vehicle_emissions_ratio *
            self.vehicle_efficiency_improvements / self.K15()
            if self.vehicleMaintenanceF29 == 2
            else 0
        )
        logging.debug("EPAGHGCalculator: J29 = %f" % res)
        return res

    def J37(self):
        """Pounds of carbon dioxide/year.

        3,071 pounds is about average for a household of one person over a year.

        =IF(naturalGasUnitH37=1,
            (naturalGasF37/Natural_gas_cost_1000CF)*EF_natural_gas*12,
            IF(naturalGasUnitH37=2,
               EF_natural_gas*naturalGasF37*12,
               IF(naturalGasUnitH37=3,
                  EF_natural_gas_therm*naturalGasF37*12)))
        """
        res = (
            self.naturalGasF37 / self.natural_gas_cost_1000CF * self.EF_natural_gas * 12
            if self.naturalGasUnitH37 == 1
            else (
                self.EF_natural_gas * self.naturalGasF37 * 12
                if self.naturalGasUnitH37 == 2
                else self.EF_natural_gas_therm * self.naturalGasF37 * 12
            )
        )
        logging.debug("EPAGHGCalculator: J37 = %f" % res)
        return res

    def J42(self):
        """Pounds of carbon dioxide equivalent/year

        5,455 pounds is about average in the U.S. for a household of one person over a year.
        
        =IF(greenPowerF45=2,
            IF(electricityUnitH42=1,
               (electricityF42/cost_per_kWh)*e_factor_value*12,
               IF(electricityUnitH42=2,
                  (electricityF42)*e_factor_value*12)),
            IF(electricityUnitH42=1,
               ((electricityF42/cost_per_kWh)*e_factor_value*12)*(1-greenPowerPercentF49),
               IF(electricityUnitH42=2,
                  (electricityF42)*12*(1-greenPowerPercentF49)*e_factor_value)))
        """
        res = (
            (
                self.electricityF42 / self.cost_per_kWh * self.e_factor_value * 12
                if self.electricityUnitH42 == 1
                else self.electricityF42 * self.e_factor_value * 12
            )
            if self.greenPowerF45 == 2
            else (
                self.electricityF42 / self.cost_per_kWh * self.e_factor_value * 12 * (
                            1 - self.greenPowerPercentF49 / 100)  # because greenPowerPercentF49 is in per cent here!
                if self.electricityUnitH42 == 1
                else self.electricityF42 * self.e_factor_value * 12 * (1 - self.greenPowerPercentF49 / 100)
            )
        )
        logging.debug("EPAGHGCalculator: J42 = %f" % res)
        return res

    def J53(self):
        """Pounds of carbon dioxide/year

        4,848 pounds is about average for a household of one person over a year. 
        
        =IF(fuelOilUnitH53=1,
            (fuelOilF53/fuel_oil_cost)*EF_fuel_oil_gallon*12,
            IF(fuelOilUnitH53=2,
            EF_fuel_oil_gallon*fuelOilF53*12))
        """
        res = (
            self.fuelOilF53 / self.fuel_oil_cost * self.EF_fuel_oil_gallon * 12
            if self.fuelOilUnitH53 == 1
            else self.EF_fuel_oil_gallon * self.fuelOilF53 * 12
        )
        logging.debug("EPAGHGCalculator: J53 = %f" % res)
        return res

    def J57(self):
        """Propane emissions
        
        Pounds of carbon dioxide/year

        2,243 pounds is about average for a household of one person over a year. 
        
        =IF(propaneUnitH57=1,
            (propaneF57/propane_cost)*EF_propane*12,
            IF(propaneUnitH57=2,EF_propane*propaneF57*12))
        """
        res = (
            self.propaneF57 / self.propane_cost * self.EF_propane * 12
            if self.propaneUnitH57 == 1
            else self.EF_propane * self.propaneF57 * 12
        )
        logging.debug("EPAGHGCalculator: J57 = %f" % res)
        return res

    def J63(self):
        """Pounds of carbon dioxide equivalent/year

        692 pounds is about average for a household of one person over a year. 

        =F5*average_waste_emissions
        """
        return self.peopleInHouseholdF5 * self.average_waste_emissions

    def J65(self):
        """Pounds of carbon dioxide equivalent/year

        =IF(recycleAluminumF65=1,$F$5*metal_recycling_avoided_emissions,0)
        """
        return (
            self.peopleInHouseholdF5 * self.metal_recycling_avoided_emissions
            if self.recycleAluminumF65 == 1
            else 0
        )

    def J67(self):
        """Pounds of carbon dioxide equivalent/year
        
        similar to J65
        """
        return self.peopleInHouseholdF5 * self.plastic_recycling_avoided_emissions if self.recyclePlasticF67 == 1 else 0

    def J69(self):
        """Pounds of carbon dioxide equivalent/year
        
        similar to J65
        """
        return self.peopleInHouseholdF5 * self.glass_recycling_avoided_emissions if self.recycleGlassF69 == 1 else 0

    def J71(self):
        """Pounds of carbon dioxide equivalent/year
        
        similar to J65
        """
        return self.peopleInHouseholdF5 \
            * self.newspaper_recycling_avoided_emissions if self.recycleNewspaperF71 == 1 else 0

    def J73(self):
        """Pounds of carbon dioxide equivalent/year
        
        similar to J65
        """
        return self.peopleInHouseholdF5 * self.mag_recycling_avoided_emissions if self.recycleMagsF73 == 1 else 0

    def J77(self):
        """Total Waste Emissions After Recycling
        
        Pounds of carbon dioxide equivalent/year

        =J63+(SUM(J65,J67,J69,J71,J73))
        """
        res = self.J63() + self.J65() + self.J67() + self.J69() + self.J71() + self.J73()
        logging.debug("EPAGHGCalculator: J77 = %f" % res)
        return res

    def co2_emissions_through_food_consumption(self):
        """Pounds of carbon dioxide equivalent/year
         food preferences contribute
         between 740 (vegan) and 1820 (heavy meat consumption) kg CO2 / year per person
        """
        return self.kgToPounds * (740 + self.foodPreferences_vegan2MeatScale * (1820 - 740))

    def co2_emissions_caused_by_flights(self):
        """We assume a fixed (and identical) CO2 emission of 88 gr / flight kilometers.
        We only distinguish between short flights (at most 1000km, average 750),
        medium flights (up to 3000 km, average 2000), and
        long flights (above 3000 km, average 7500)
        """

        co2_in_kg = self.mobility_airplane_short_flights * self.get_average_co2_per_flight_type('short') + \
            self.mobility_airplane_medium_flights * self.get_average_co2_per_flight_type('medium') + \
            self.mobility_airplane_long_flights * self.get_average_co2_per_flight_type('long')
        return self.kgToPounds * co2_in_kg

    def get_average_co2_per_flight_type(self, flight_type):
        return self.flights_average_km_and_costs[flight_type]['kilometersPerTrip'] * \
               self.flights_average_km_and_costs[flight_type]['co2PerKilometerInKG']

    def J82(self):
        """Your Total Emissions

        Pounds of carbon dioxide equivalent/year

        =SUM(J26,J37,J42,J53,J57,J77)
        """
        res = self.J26() + self.J37() + self.J42() + self.J53() + self.J57() + self.J77()
        res = res + self.co2_emissions_through_food_consumption() + self.co2_emissions_caused_by_flights()
        logging.debug("EPAGHGCalculator: J82 = %f" % res)
        return res

        # TODO: add reduction potential from rows 87 on!

    def calculate(self, input_dict):
        for (key, pair) in self.input_labels_defaults.items():
            label, default = pair
            logging.debug("EPAGHGCalculator: default value for key " + key + " (" + label + ") is " + str(default))
            setattr(self, key, default)
        for (key, value) in input_dict.items():
            if key in self.input_labels_defaults.keys():
                # label, default = self.input_labels_defaults[key]
                if value is not None:
                    logging.debug("EPAGHGCalculator: actual value for key %s submitted as %s" % (key, str(value)))
                    setattr(self, key, value)
                else:
                    logging.warning("EPAGHGCalculator: 'None' value submitted for key %s, sticking to default" % key)
            else:
                logging.warning("EPAGHGCalculator:  key '%s' unknown, with value: %s" % (str(key), str(value)))

        logging.info("EPAGHGCalculator: calculating")
        total_carbon_emissions = self.J82()
        result = (f"""
            due to driving {(100 * self.J26() / total_carbon_emissions):2.2f}%,
            due to natural gas {(100 * self.J37() / total_carbon_emissions):2.2f}%, 
            due to electricity {(100 * self.J42() / total_carbon_emissions):2.2f}%, 
            due to fuel oil {(100 * self.J53() / total_carbon_emissions):2.2f}%, 
            due to propane {(100 * self.J57() / total_carbon_emissions):2.2f}%, 
            due to waste after recycling {(100 * self.J77() / total_carbon_emissions):2.2f}%, 
            due to flights {(100 * self.co2_emissions_caused_by_flights() / total_carbon_emissions):2.2f}%, 
            due to food {(100 * self.co2_emissions_through_food_consumption() / total_carbon_emissions):2.2f}%, 
            total carbon emissions {(total_carbon_emissions * self.poundsCO2eq_to_GtC)}[GtC/yr]
            """
        )
        logging.info("EPAGHGCalculator computed carbon emissions:  " + str(result))
        return total_carbon_emissions * self.poundsCO2eq_to_GtC


default_ePACarbonFootprintCalculatorInput = {
    k: v[1]
    for (k, v) in EPAGHGCalculator.input_labels_defaults.items()
}
"""default input of new Agents"""

# if __name__ == "__main__":
#     logger = logging.getLogger("Test")
#     logger.setLevel(20)
#     logger.info("Running EPAGHGCalculator Test")
#     epa_calculator = EPAGHGCalculator()
#     logger.info("Default values: ")
#     logger.info(str(epa_calculator.calculate(dict())))

#     logger.info("Vegan: ")
#     input_data = dict()
#     input_data["foodPreferences_vegan2MeatScale"] = 0
#     logger.info(str(epa_calculator.calculate(input_data)))

#     logger.info("Miles / year * 2.1: ")
#     input_data = dict()
#     input_data["vehicle1MilesD15"] = epa_calculator.input_labels_defaults["vehicle1MilesD15"][1] * 2.1
#     logger.info(str(epa_calculator.calculate(input_data)))

#     logger.info("Miles / year / 30 per week ")
#     input_data = dict()
#     input_data["vehicle1MilesD15"] = epa_calculator.input_labels_defaults["vehicle1MilesD15"][1] / 30
#     input_data["vehicle1MilesUnitG15"] = 1
#     logger.info(str(epa_calculator.calculate(input_data)))

#     logger.info("1/2/3 flights")
#     input_data = dict()
#     input_data["mobility_airplane_short_flights"] = 1
#     input_data["mobility_airplane_medium_flights"] = 2
#     input_data["mobility_airplane_long_flights"] = 3
#     epa_calculator.flights_average_km_and_costs = {'short': {'kilometersPerTrip': 750, 'co2PerKilometerInKG': 0.088},
#                                     'medium': {'kilometersPerTrip': 2000, 'co2PerKilometerInKG': 0.088},
#                                     'long': {'kilometersPerTrip': 7500, 'co2PerKilometerInKG': 0.088}}

#     logger.info(str(epa_calculator.calculate(input_data)))

#     logger.info("without recycling")
#     input_data = dict()
#     input_data["recycleAluminumF65"] = 2
#     input_data["recyclePlasticF67"] = 2
#     input_data["recycleGlassF69"] = 2
#     input_data["recycleNewspaperF71"] = 2
#     input_data["recycleMagsF73"] = 2
#     logger.info(str(epa_calculator.calculate(input_data)))

#     logger.info("EPAGHGCalculator Test: calling exit()")
#     exit()


def calculate_co2(sample):
    epa_calculator = EPAGHGCalculator()

    epa_calculator.flights_average_km_and_costs = {
        'short': {'kilometersPerTrip': 750, 'co2PerKilometerInKG': 0.088},
        'medium': {'kilometersPerTrip': 2000, 'co2PerKilometerInKG': 0.088},
        'long': {'kilometersPerTrip': 7500, 'co2PerKilometerInKG': 0.088}
    }

    footprint_list = []

    for s in sample:
        input_data = dict()

        # Recycling 
        # Transforms binary values into 1/2
        input_data["recyclePlasticF67"] = 1 if s[0] else 2
        input_data["recycleGlassF69"] = 1 if s[1] else 2
        input_data["recycleMagsF73"] = 1 if s[2] else 2
        input_data["recycleNewspaperF71"] = 1 if s[3] else 2
        input_data["recycleAluminumF65"] = 1 if s[4] else 2

        # Mobility
        # Converts kilometers into miles
        #input_data = 1 if s[0] else 2
        input_data["vehicle1MilesD15"] = s[5] / 1.609

        # Mobility (planes)
        # Takes number of flights
        input_data["mobility_airplane_short_flights"] = s[6]
        input_data["mobility_airplane_medium_flights"] = s[7]
        input_data["mobility_airplane_long_flights"] = s[8]

        # Diet
        # Takes value in [0,1]
        input_data["foodPreferences_vegan2MeatScale"] = s[13]

        footprint = epa_calculator.calculate(input_data)
        footprint_list.append(footprint)

    return footprint_list
