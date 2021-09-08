from pydoc import locate
from src.archemist.state import material, station
from src.archemist.state.result import Result
from src.archemist.state.recipe import StationFlow, StationFlowNode, Recipe
from src.archemist.persistence.dbHandler import dbHandler
from src.archemist.persistence.fsHandler import FSHandler
from src.archemist.state.robot import mobileRobot, armRobot
import src.archemist.state.robots
import src.archemist.state.stations
from datetime import date, timedelta
import datetime
from multipledispatch import dispatch
import os
import sys

class Parser:

    @dispatch()
    def loadRecipeYaml(self):
        __location__ = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))
        handler = FSHandler()
        return self.loadRecipeYaml(handler.loadYamlFile(os.path.join(__location__, 'workflowConfigs\\recipes\\recipe.yaml')))

    @dispatch(dict)
    def loadRecipeYaml(self, recipeDictionary):
        config = self.loadConfigYaml()

        liquidsList = list()
        for liquid in recipeDictionary["recipe"]["materials"]["liquids"]:
            for liquidMaterial in config[0]:
                if str(liquidMaterial.name) == liquid:
                    liquidsList.append(liquidMaterial)


        solidsList = list()
        for solid in recipeDictionary["recipe"]["materials"]["solids"]:
            for solidMaterial in config[1]:
                if str(solidMaterial.name) == solid:
                    solidsList.append(solidMaterial)

        stationFlowList = list()
        for state, stateList in recipeDictionary["recipe"]["stationFlow"].items():
            for stateData in stateList:
                stationF = None
                for flowStation in config[3]:
                    if str(flowStation.name) == stateList["station"]:
                        stationF = flowStation

            stationFlowList.append(StationFlowNode(
                state, stationF, stateList["task"], stateList["onsuccess"], stateList["onfail"]))

        stationOpDescriptors = list()
        for stationopdesc in recipeDictionary["recipe"]["stationOps"]:
            stationOp = type(stationopdesc, (station.StationOpDescriptor, ),
                               recipeDictionary["recipe"]["stationOps"][stationopdesc])
            stationOpDescriptors.append(stationOp)

        stationflow = StationFlow(stationFlowList)

        newRecipe = Recipe(recipeDictionary["recipe"]["name"], recipeDictionary["recipe"]["id"], stationOpDescriptors,
        stationflow, solidsList, liquidsList)
        return newRecipe

    @dispatch()
    def loadConfigYaml(self):
        handler = dbHandler()
        config = dict()
        config = {'workflow': handler.getConfig()}
        return self.loadConfigYaml(config)

    @dispatch(dict)
    def loadConfigYaml(self, configDictionaryInput):
        # Get rid of top-level workflow key, only interested in everything below
        configDictionary = configDictionaryInput["workflow"]
        configList = list()  # list of lists, for each category of config

        liquids = list()  # list of liquids
        # loop through each key under "liquids"
        for liquid in configDictionary["Materials"]["liquids"]:
            # Set default expiration date to 3 weeks from now, in case one isn't set
            exp_date = date.today() + timedelta(days=21)
            # if expiry date is set then parse string to date type
            if "expiry_date" in configDictionary["Materials"]["liquids"][liquid]:
                exp_date = datetime.strptime(
                    configDictionary["Materials"]["liquids"][liquid]["expiry_date"], '%d/%m/%y %H:%M:%S')
            # convert between volume and mass using density. Density must be set
            vol = 0
            mass = 0
            dens = configDictionary["Materials"]["liquids"][liquid]["density"]
            # Also convert for every possible unit, mg, g, ug, ml, l and ul
            if configDictionary["Materials"]["liquids"][liquid]["unit"] == "mg":
                mass = configDictionary["Materials"]["liquids"][liquid]["amount_stored"]/1000
                vol = mass/dens
            elif configDictionary["Materials"]["liquids"][liquid]["unit"] == "g":
                mass = configDictionary["Materials"]["liquids"][liquid]["amount_stored"]
                vol = mass/dens
            elif configDictionary["Materials"]["liquids"][liquid]["unit"] == "ug":
                mass = configDictionary["Materials"]["liquids"][liquid]["amount_stored"]/1000/1000
                vol = mass/dens
            elif configDictionary["Materials"]["liquids"][liquid]["unit"] == "ml":
                vol = configDictionary["Materials"]["liquids"][liquid]["amount_stored"]/1000
                mass = vol*dens
            elif configDictionary["Materials"]["liquids"][liquid]["unit"] == "l":
                vol = configDictionary["Materials"]["liquids"][liquid]["amount_stored"]
                mass = vol*dens
            elif configDictionary["Materials"]["liquids"][liquid]["unit"] == "ul":
                vol = configDictionary["Materials"]["liquids"][liquid]["amount_stored"]/1000/1000
                mass = vol*dens

            # other liquid properties added directly from yaml
            liquids.append(material.Liquid(
                liquid, configDictionary["Materials"]["liquids"][liquid]["id"], exp_date, mass, dens, vol))
        configList.append(liquids)

        solids = list()  # list of solids to be used
        for solid in configDictionary["Materials"]["solids"]:
            # default expiration date if not set
            exp_date = date.today() + timedelta(days=21)
            # if set, parse string to date
            if "expiry_date" in configDictionary["Materials"]["solids"][solid]:
                exp_date = datetime.tstrptime(
                    configDictionary["Materials"]["solids"][solid]["expiry_date"], '%d/%m/%y %H:%M:%S')

            mass = 0  # convert between mass units to universal grams
            if configDictionary["Materials"]["solids"][solid]["unit"] == "mg":
                mass = configDictionary["Materials"]["solids"][solid]["amount_stored"]/1000
            elif configDictionary["Materials"]["solids"][solid]["unit"] == "g":
                mass = configDictionary["Materials"]["solids"][solid]["amount_stored"]
            elif configDictionary["Materials"]["solids"][solid]["unit"] == "ug":
                mass = configDictionary["Materials"]["solids"][solid]["amount_stored"]/1000/1000

            # Add solid to list of solids
            solids.append(material.Solid(solid, configDictionary["Materials"]["solids"][solid]["id"],
                          exp_date, mass, configDictionary["Materials"]["solids"][solid]["dispense_method"]))
        configList.append(solids)

        robots = list()  # list of batches
        for robot in configDictionary["Robots"]:
            robotObj = self.str_to_class_robot(configDictionary["Robots"][robot]["type"])
            robotObj = robotObj(robot, configDictionary["Robots"][robot]["id"])
            robots.append(robotObj)
        configList.append(robots)

        stations = list()  # list of stations
        for stationN in configDictionary["Stations"]:
            stationObj = self.str_to_class_station(stationN)
            location = station.Location(configDictionary["Stations"][stationN]["location"]["node_id"], configDictionary["Stations"][stationN]["location"]["graph_id"], configDictionary["Stations"][stationN]["location"]["map_id"])
            stationObj = stationObj(stationN, configDictionary["Stations"][stationN]["id"], location)
            # set dictionary entry to the location object (instead of name string)
            # newstation = type(stationN, (station.Station, ),
            #                   configDictionary["Stations"][stationN])
            # create object of new station class, passing parameters from yaml and also using location object
            stations.append(stationObj)
        configList.append(stations)  # add to list of lists

        ##todo: parse station op descriptors from config, to be applied in stationflownodes in recipe

        results = list()  # create list of result/output specification from yaml
        for resultI in configDictionary["OutputDescriptors"]:
            resultN = Result(resultI, configDictionary["OutputDescriptors"][resultI]["characteristic"], locate(
                configDictionary["OutputDescriptors"][resultI]["type"]))
            results.append(resultN)
        configList.append(results)  # add to list of lists

        return configList  # finally return list

    def str_to_class_robot(self, classname):
      return getattr(src.archemist.state.robots, classname)

    def str_to_class_station(self, classname):
      return getattr(src.archemist.state.stations, classname)
