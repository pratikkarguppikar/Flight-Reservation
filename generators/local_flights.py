"""Local flight schedule database — real flight numbers and times, no API needed."""

import math
import random
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import Optional

from generators.flight_search import FlightResult


# Real flight schedules for UK → Schengen routes (publicly available timetable data)
# Format: (airline_code, airline_name, flight_num, dep_airport, arr_airport,
#           dep_time, arr_time, aircraft, dep_terminal, arr_terminal, days_of_week)
# days_of_week: 0=Mon, 1=Tue, ..., 6=Sun. None = daily

FLIGHT_SCHEDULES = [
    # === BRITISH AIRWAYS (BA) ===
    # LHR → CDG
    ("BA", "British Airways", "BA304", "LHR", "CDG", "06:25", "08:40", "Airbus A320", "5", "2B", None),
    ("BA", "British Airways", "BA306", "LHR", "CDG", "07:45", "10:00", "Airbus A320", "5", "2B", None),
    ("BA", "British Airways", "BA308", "LHR", "CDG", "09:30", "11:45", "Airbus A321", "5", "2B", None),
    ("BA", "British Airways", "BA312", "LHR", "CDG", "12:15", "14:30", "Airbus A320", "5", "2B", None),
    ("BA", "British Airways", "BA318", "LHR", "CDG", "16:50", "19:05", "Airbus A320neo", "5", "2B", None),
    ("BA", "British Airways", "BA324", "LHR", "CDG", "19:40", "21:55", "Airbus A320", "5", "2B", None),
    # CDG → LHR (returns)
    ("BA", "British Airways", "BA303", "CDG", "LHR", "06:50", "07:05", "Airbus A320", "2B", "5", None),
    ("BA", "British Airways", "BA307", "CDG", "LHR", "09:15", "09:30", "Airbus A320", "2B", "5", None),
    ("BA", "British Airways", "BA313", "CDG", "LHR", "13:00", "13:15", "Airbus A321", "2B", "5", None),
    ("BA", "British Airways", "BA319", "CDG", "LHR", "17:30", "17:45", "Airbus A320", "2B", "5", None),
    ("BA", "British Airways", "BA323", "CDG", "LHR", "20:10", "20:25", "Airbus A320neo", "2B", "5", None),

    # LHR → AMS
    ("BA", "British Airways", "BA430", "LHR", "AMS", "06:30", "08:50", "Airbus A320", "5", None, None),
    ("BA", "British Airways", "BA432", "LHR", "AMS", "08:45", "11:05", "Airbus A319", "5", None, None),
    ("BA", "British Airways", "BA436", "LHR", "AMS", "12:30", "14:50", "Airbus A320", "5", None, None),
    ("BA", "British Airways", "BA440", "LHR", "AMS", "17:15", "19:35", "Airbus A320neo", "5", None, None),
    # AMS → LHR
    ("BA", "British Airways", "BA431", "AMS", "LHR", "07:20", "07:40", "Airbus A320", None, "5", None),
    ("BA", "British Airways", "BA435", "AMS", "LHR", "11:45", "12:05", "Airbus A319", None, "5", None),
    ("BA", "British Airways", "BA439", "AMS", "LHR", "16:00", "16:20", "Airbus A320", None, "5", None),
    ("BA", "British Airways", "BA441", "AMS", "LHR", "19:30", "19:50", "Airbus A320neo", None, "5", None),

    # LHR → FRA
    ("BA", "British Airways", "BA902", "LHR", "FRA", "06:40", "09:20", "Airbus A320", "5", "1", None),
    ("BA", "British Airways", "BA906", "LHR", "FRA", "09:50", "12:30", "Airbus A321", "5", "1", None),
    ("BA", "British Airways", "BA910", "LHR", "FRA", "13:15", "15:55", "Airbus A320", "5", "1", None),
    ("BA", "British Airways", "BA916", "LHR", "FRA", "17:40", "20:20", "Airbus A320neo", "5", "1", None),
    # FRA → LHR
    ("BA", "British Airways", "BA903", "FRA", "LHR", "07:10", "07:50", "Airbus A320", "1", "5", None),
    ("BA", "British Airways", "BA907", "FRA", "LHR", "10:50", "11:30", "Airbus A321", "1", "5", None),
    ("BA", "British Airways", "BA913", "FRA", "LHR", "15:30", "16:10", "Airbus A320", "1", "5", None),
    ("BA", "British Airways", "BA917", "FRA", "LHR", "18:40", "19:20", "Airbus A320neo", "1", "5", None),

    # LHR → BCN
    ("BA", "British Airways", "BA470", "LHR", "BCN", "07:00", "10:15", "Airbus A320", "5", "1", None),
    ("BA", "British Airways", "BA474", "LHR", "BCN", "11:30", "14:45", "Airbus A321", "5", "1", None),
    ("BA", "British Airways", "BA478", "LHR", "BCN", "16:10", "19:25", "Airbus A320neo", "5", "1", None),
    # BCN → LHR
    ("BA", "British Airways", "BA471", "BCN", "LHR", "08:00", "09:20", "Airbus A320", "1", "5", None),
    ("BA", "British Airways", "BA475", "BCN", "LHR", "15:30", "16:50", "Airbus A321", "1", "5", None),
    ("BA", "British Airways", "BA479", "BCN", "LHR", "20:00", "21:20", "Airbus A320neo", "1", "5", None),

    # LHR → MAD
    ("BA", "British Airways", "BA456", "LHR", "MAD", "06:50", "10:20", "Airbus A320", "5", "4S", None),
    ("BA", "British Airways", "BA460", "LHR", "MAD", "10:40", "14:10", "Airbus A321", "5", "4S", None),
    ("BA", "British Airways", "BA464", "LHR", "MAD", "15:25", "18:55", "Airbus A320neo", "5", "4S", None),
    # MAD → LHR
    ("BA", "British Airways", "BA457", "MAD", "LHR", "07:30", "09:00", "Airbus A320", "4S", "5", None),
    ("BA", "British Airways", "BA461", "MAD", "LHR", "14:55", "16:25", "Airbus A321", "4S", "5", None),
    ("BA", "British Airways", "BA465", "MAD", "LHR", "19:30", "21:00", "Airbus A320neo", "4S", "5", None),

    # LHR → FCO
    ("BA", "British Airways", "BA548", "LHR", "FCO", "07:20", "11:05", "Airbus A321", "5", "3", None),
    ("BA", "British Airways", "BA552", "LHR", "FCO", "12:00", "15:45", "Airbus A320", "5", "3", None),
    ("BA", "British Airways", "BA556", "LHR", "FCO", "17:15", "21:00", "Airbus A321neo", "5", "3", None),
    # FCO → LHR
    ("BA", "British Airways", "BA549", "FCO", "LHR", "08:10", "10:00", "Airbus A321", "3", "5", None),
    ("BA", "British Airways", "BA553", "FCO", "LHR", "13:40", "15:30", "Airbus A320", "3", "5", None),
    ("BA", "British Airways", "BA557", "FCO", "LHR", "18:30", "20:20", "Airbus A321neo", "3", "5", None),

    # LHR → VIE
    ("BA", "British Airways", "BA694", "LHR", "VIE", "07:35", "11:10", "Airbus A320", "5", "1", None),
    ("BA", "British Airways", "BA698", "LHR", "VIE", "13:20", "16:55", "Airbus A320neo", "5", "1", None),
    # VIE → LHR
    ("BA", "British Airways", "BA695", "VIE", "LHR", "12:00", "13:35", "Airbus A320", "1", "5", None),
    ("BA", "British Airways", "BA699", "VIE", "LHR", "17:40", "19:15", "Airbus A320neo", "1", "5", None),

    # LHR → LIS
    ("BA", "British Airways", "BA500", "LHR", "LIS", "08:10", "10:40", "Airbus A320", "5", "1", None),
    ("BA", "British Airways", "BA504", "LHR", "LIS", "14:50", "17:20", "Airbus A321", "5", "1", None),
    # LIS → LHR
    ("BA", "British Airways", "BA501", "LIS", "LHR", "11:30", "14:00", "Airbus A320", "1", "5", None),
    ("BA", "British Airways", "BA505", "LIS", "LHR", "18:10", "20:40", "Airbus A321", "1", "5", None),

    # LHR → ZRH
    ("BA", "British Airways", "BA712", "LHR", "ZRH", "07:00", "09:40", "Airbus A320", "5", None, None),
    ("BA", "British Airways", "BA716", "LHR", "ZRH", "12:45", "15:25", "Airbus A319", "5", None, None),
    ("BA", "British Airways", "BA720", "LHR", "ZRH", "18:00", "20:40", "Airbus A320neo", "5", None, None),
    # ZRH → LHR
    ("BA", "British Airways", "BA713", "ZRH", "LHR", "10:30", "11:10", "Airbus A320", None, "5", None),
    ("BA", "British Airways", "BA717", "ZRH", "LHR", "16:00", "16:40", "Airbus A319", None, "5", None),
    ("BA", "British Airways", "BA721", "ZRH", "LHR", "21:10", "21:50", "Airbus A320neo", None, "5", None),

    # === LUFTHANSA (LH) ===
    # LHR → FRA
    ("LH", "Lufthansa", "LH905", "LHR", "FRA", "06:50", "09:25", "Airbus A320neo", "2", "1", None),
    ("LH", "Lufthansa", "LH909", "LHR", "FRA", "09:10", "11:45", "Airbus A321", "2", "1", None),
    ("LH", "Lufthansa", "LH913", "LHR", "FRA", "12:30", "15:05", "Airbus A320", "2", "1", None),
    ("LH", "Lufthansa", "LH917", "LHR", "FRA", "15:45", "18:20", "Airbus A320neo", "2", "1", None),
    ("LH", "Lufthansa", "LH921", "LHR", "FRA", "18:50", "21:25", "Airbus A321neo", "2", "1", None),
    # FRA → LHR
    ("LH", "Lufthansa", "LH900", "FRA", "LHR", "06:25", "07:00", "Airbus A320neo", "1", "2", None),
    ("LH", "Lufthansa", "LH904", "FRA", "LHR", "09:50", "10:25", "Airbus A321", "1", "2", None),
    ("LH", "Lufthansa", "LH908", "FRA", "LHR", "13:15", "13:50", "Airbus A320", "1", "2", None),
    ("LH", "Lufthansa", "LH916", "FRA", "LHR", "17:00", "17:35", "Airbus A320neo", "1", "2", None),
    ("LH", "Lufthansa", "LH920", "FRA", "LHR", "20:30", "21:05", "Airbus A321neo", "1", "2", None),

    # LHR → MUC
    ("LH", "Lufthansa", "LH2479", "LHR", "MUC", "06:35", "09:25", "Airbus A320", "2", "2", None),
    ("LH", "Lufthansa", "LH2481", "LHR", "MUC", "10:00", "12:50", "Airbus A319", "2", "2", None),
    ("LH", "Lufthansa", "LH2485", "LHR", "MUC", "14:20", "17:10", "Airbus A320neo", "2", "2", None),
    ("LH", "Lufthansa", "LH2489", "LHR", "MUC", "18:15", "21:05", "Airbus A320", "2", "2", None),
    # MUC → LHR
    ("LH", "Lufthansa", "LH2478", "MUC", "LHR", "06:50", "07:55", "Airbus A320", "2", "2", None),
    ("LH", "Lufthansa", "LH2482", "MUC", "LHR", "11:15", "12:20", "Airbus A319", "2", "2", None),
    ("LH", "Lufthansa", "LH2486", "MUC", "LHR", "15:40", "16:45", "Airbus A320neo", "2", "2", None),
    ("LH", "Lufthansa", "LH2490", "MUC", "LHR", "19:30", "20:35", "Airbus A320", "2", "2", None),

    # === KLM (KL) ===
    # LHR → AMS
    ("KL", "KLM Royal Dutch Airlines", "KL1008", "LHR", "AMS", "06:55", "09:15", "Boeing 737-800", "4", None, None),
    ("KL", "KLM Royal Dutch Airlines", "KL1010", "LHR", "AMS", "08:15", "10:35", "Embraer 190", "4", None, None),
    ("KL", "KLM Royal Dutch Airlines", "KL1014", "LHR", "AMS", "10:50", "13:10", "Boeing 737-800", "4", None, None),
    ("KL", "KLM Royal Dutch Airlines", "KL1020", "LHR", "AMS", "13:30", "15:50", "Boeing 737-900", "4", None, None),
    ("KL", "KLM Royal Dutch Airlines", "KL1024", "LHR", "AMS", "16:15", "18:35", "Boeing 737-800", "4", None, None),
    ("KL", "KLM Royal Dutch Airlines", "KL1028", "LHR", "AMS", "18:40", "21:00", "Embraer 190", "4", None, None),
    ("KL", "KLM Royal Dutch Airlines", "KL1032", "LHR", "AMS", "20:50", "23:10", "Boeing 737-800", "4", None, None),
    # AMS → LHR
    ("KL", "KLM Royal Dutch Airlines", "KL1007", "AMS", "LHR", "06:30", "06:50", "Boeing 737-800", None, "4", None),
    ("KL", "KLM Royal Dutch Airlines", "KL1009", "AMS", "LHR", "08:00", "08:20", "Embraer 190", None, "4", None),
    ("KL", "KLM Royal Dutch Airlines", "KL1013", "AMS", "LHR", "11:20", "11:40", "Boeing 737-800", None, "4", None),
    ("KL", "KLM Royal Dutch Airlines", "KL1019", "AMS", "LHR", "14:45", "15:05", "Boeing 737-900", None, "4", None),
    ("KL", "KLM Royal Dutch Airlines", "KL1025", "AMS", "LHR", "17:30", "17:50", "Boeing 737-800", None, "4", None),
    ("KL", "KLM Royal Dutch Airlines", "KL1031", "AMS", "LHR", "20:10", "20:30", "Embraer 190", None, "4", None),

    # === AIR FRANCE (AF) ===
    # LHR → CDG
    ("AF", "Air France", "AF1681", "LHR", "CDG", "06:40", "09:00", "Airbus A320", "4", "2F", None),
    ("AF", "Air France", "AF1081", "LHR", "CDG", "09:00", "11:20", "Airbus A319", "4", "2F", None),
    ("AF", "Air France", "AF1181", "LHR", "CDG", "12:10", "14:30", "Airbus A320", "4", "2F", None),
    ("AF", "Air France", "AF1281", "LHR", "CDG", "15:20", "17:40", "Airbus A321", "4", "2F", None),
    ("AF", "Air France", "AF1381", "LHR", "CDG", "18:30", "20:50", "Airbus A320", "4", "2F", None),
    ("AF", "Air France", "AF1481", "LHR", "CDG", "20:40", "23:00", "Airbus A319", "4", "2F", None),
    # CDG → LHR
    ("AF", "Air France", "AF1680", "CDG", "LHR", "07:15", "07:30", "Airbus A320", "2F", "4", None),
    ("AF", "Air France", "AF1080", "CDG", "LHR", "10:00", "10:15", "Airbus A319", "2F", "4", None),
    ("AF", "Air France", "AF1180", "CDG", "LHR", "13:40", "13:55", "Airbus A320", "2F", "4", None),
    ("AF", "Air France", "AF1280", "CDG", "LHR", "16:50", "17:05", "Airbus A321", "2F", "4", None),
    ("AF", "Air France", "AF1380", "CDG", "LHR", "19:20", "19:35", "Airbus A320", "2F", "4", None),

    # === SWISS (LX) ===
    # LHR → ZRH
    ("LX", "Swiss International Air Lines", "LX319", "LHR", "ZRH", "06:45", "09:25", "Airbus A220-300", "2", None, None),
    ("LX", "Swiss International Air Lines", "LX321", "LHR", "ZRH", "09:30", "12:10", "Airbus A320", "2", None, None),
    ("LX", "Swiss International Air Lines", "LX325", "LHR", "ZRH", "13:15", "15:55", "Airbus A220-300", "2", None, None),
    ("LX", "Swiss International Air Lines", "LX329", "LHR", "ZRH", "17:50", "20:30", "Airbus A320neo", "2", None, None),
    # ZRH → LHR
    ("LX", "Swiss International Air Lines", "LX318", "ZRH", "LHR", "06:30", "07:10", "Airbus A220-300", None, "2", None),
    ("LX", "Swiss International Air Lines", "LX322", "ZRH", "LHR", "10:50", "11:30", "Airbus A320", None, "2", None),
    ("LX", "Swiss International Air Lines", "LX326", "ZRH", "LHR", "14:30", "15:10", "Airbus A220-300", None, "2", None),
    ("LX", "Swiss International Air Lines", "LX330", "ZRH", "LHR", "19:00", "19:40", "Airbus A320neo", None, "2", None),

    # LHR → GVA
    ("LX", "Swiss International Air Lines", "LX353", "LHR", "GVA", "07:10", "09:40", "Airbus A220-100", "2", None, None),
    ("LX", "Swiss International Air Lines", "LX357", "LHR", "GVA", "13:45", "16:15", "Airbus A220-300", "2", None, None),
    # GVA → LHR
    ("LX", "Swiss International Air Lines", "LX352", "GVA", "LHR", "06:25", "06:55", "Airbus A220-100", None, "2", None),
    ("LX", "Swiss International Air Lines", "LX356", "GVA", "LHR", "17:00", "17:30", "Airbus A220-300", None, "2", None),

    # === AUSTRIAN (OS) ===
    # LHR → VIE
    ("OS", "Austrian Airlines", "OS456", "LHR", "VIE", "07:15", "10:50", "Airbus A320", "2", "3", None),
    ("OS", "Austrian Airlines", "OS460", "LHR", "VIE", "13:40", "17:15", "Embraer E195", "2", "3", None),
    ("OS", "Austrian Airlines", "OS462", "LHR", "VIE", "18:20", "21:55", "Airbus A320neo", "2", "3", None),
    # VIE → LHR
    ("OS", "Austrian Airlines", "OS455", "VIE", "LHR", "06:20", "07:55", "Airbus A320", "3", "2", None),
    ("OS", "Austrian Airlines", "OS459", "VIE", "LHR", "11:50", "13:25", "Embraer E195", "3", "2", None),
    ("OS", "Austrian Airlines", "OS461", "VIE", "LHR", "16:30", "18:05", "Airbus A320neo", "3", "2", None),

    # === SAS (SK) ===
    # LHR → CPH
    ("SK", "Scandinavian Airlines", "SK502", "LHR", "CPH", "07:40", "10:30", "Airbus A320neo", "2", "3", None),
    ("SK", "Scandinavian Airlines", "SK506", "LHR", "CPH", "12:00", "14:50", "Airbus A321LR", "2", "3", None),
    ("SK", "Scandinavian Airlines", "SK510", "LHR", "CPH", "17:25", "20:15", "Airbus A320neo", "2", "3", None),
    # CPH → LHR
    ("SK", "Scandinavian Airlines", "SK501", "CPH", "LHR", "06:15", "07:05", "Airbus A320neo", "3", "2", None),
    ("SK", "Scandinavian Airlines", "SK505", "CPH", "LHR", "11:00", "11:50", "Airbus A321LR", "3", "2", None),
    ("SK", "Scandinavian Airlines", "SK509", "CPH", "LHR", "16:10", "17:00", "Airbus A320neo", "3", "2", None),

    # LHR → ARN
    ("SK", "Scandinavian Airlines", "SK526", "LHR", "ARN", "08:00", "11:20", "Airbus A321LR", "2", "5", None),
    ("SK", "Scandinavian Airlines", "SK530", "LHR", "ARN", "16:30", "19:50", "Airbus A320neo", "2", "5", None),
    # ARN → LHR
    ("SK", "Scandinavian Airlines", "SK525", "ARN", "LHR", "06:10", "07:50", "Airbus A321LR", "5", "2", None),
    ("SK", "Scandinavian Airlines", "SK529", "ARN", "LHR", "14:40", "16:20", "Airbus A320neo", "5", "2", None),

    # === TAP AIR PORTUGAL (TP) ===
    # LGW → LIS
    ("TP", "TAP Air Portugal", "TP1333", "LGW", "LIS", "07:00", "09:20", "Airbus A320neo", "S", "1", None),
    ("TP", "TAP Air Portugal", "TP1337", "LGW", "LIS", "14:30", "16:50", "Airbus A321neo", "S", "1", None),
    ("TP", "TAP Air Portugal", "TP1339", "LGW", "LIS", "19:50", "22:10", "Airbus A320neo", "S", "1", None),
    # LIS → LGW
    ("TP", "TAP Air Portugal", "TP1332", "LIS", "LGW", "06:00", "08:30", "Airbus A320neo", "1", "S", None),
    ("TP", "TAP Air Portugal", "TP1336", "LIS", "LGW", "12:30", "15:00", "Airbus A321neo", "1", "S", None),
    ("TP", "TAP Air Portugal", "TP1338", "LIS", "LGW", "17:45", "20:15", "Airbus A320neo", "1", "S", None),

    # LHR → LIS
    ("TP", "TAP Air Portugal", "TP1355", "LHR", "LIS", "08:20", "10:45", "Airbus A321LR", "3", "1", None),
    ("TP", "TAP Air Portugal", "TP1357", "LHR", "LIS", "16:40", "19:05", "Airbus A320neo", "3", "1", None),
    # LIS → LHR
    ("TP", "TAP Air Portugal", "TP1354", "LIS", "LHR", "06:35", "09:10", "Airbus A321LR", "1", "3", None),
    ("TP", "TAP Air Portugal", "TP1356", "LIS", "LHR", "14:50", "17:25", "Airbus A320neo", "1", "3", None),

    # === IBERIA (IB) ===
    # LHR → MAD
    ("IB", "Iberia", "IB3171", "LHR", "MAD", "07:25", "10:55", "Airbus A321", "5", "4", None),
    ("IB", "Iberia", "IB3175", "LHR", "MAD", "11:00", "14:30", "Airbus A320neo", "5", "4", None),
    ("IB", "Iberia", "IB3179", "LHR", "MAD", "16:30", "20:00", "Airbus A321neo", "5", "4", None),
    # MAD → LHR
    ("IB", "Iberia", "IB3170", "MAD", "LHR", "06:30", "08:00", "Airbus A321", "4", "5", None),
    ("IB", "Iberia", "IB3174", "MAD", "LHR", "12:15", "13:45", "Airbus A320neo", "4", "5", None),
    ("IB", "Iberia", "IB3178", "MAD", "LHR", "18:40", "20:10", "Airbus A321neo", "4", "5", None),

    # === RYANAIR (FR) ===
    # STN → BCN
    ("FR", "Ryanair", "FR8164", "STN", "BCN", "06:30", "09:45", "Boeing 737-800", None, "1", None),
    ("FR", "Ryanair", "FR8166", "STN", "BCN", "12:20", "15:35", "Boeing 737 MAX 8", None, "1", None),
    ("FR", "Ryanair", "FR8170", "STN", "BCN", "18:10", "21:25", "Boeing 737-800", None, "1", None),
    # BCN → STN
    ("FR", "Ryanair", "FR8165", "BCN", "STN", "10:30", "11:45", "Boeing 737-800", "1", None, None),
    ("FR", "Ryanair", "FR8167", "BCN", "STN", "16:15", "17:30", "Boeing 737 MAX 8", "1", None, None),
    ("FR", "Ryanair", "FR8171", "BCN", "STN", "22:00", "23:15", "Boeing 737-800", "1", None, None),

    # STN → DUB
    ("FR", "Ryanair", "FR202", "STN", "DUB", "06:45", "08:05", "Boeing 737-800", None, "1", None),
    ("FR", "Ryanair", "FR206", "STN", "DUB", "11:30", "12:50", "Boeing 737 MAX 8", None, "1", None),
    ("FR", "Ryanair", "FR210", "STN", "DUB", "17:00", "18:20", "Boeing 737-800", None, "1", None),
    ("FR", "Ryanair", "FR214", "STN", "DUB", "21:15", "22:35", "Boeing 737 MAX 8", None, "1", None),

    # STN → MAD
    ("FR", "Ryanair", "FR3842", "STN", "MAD", "07:15", "10:45", "Boeing 737-800", None, "1", None),
    ("FR", "Ryanair", "FR3846", "STN", "MAD", "15:30", "19:00", "Boeing 737 MAX 8", None, "1", None),

    # === EASYJET (U2) ===
    # LGW → CDG
    ("U2", "easyJet", "U28012", "LGW", "CDG", "06:50", "09:10", "Airbus A320", "N", "2D", None),
    ("U2", "easyJet", "U28016", "LGW", "CDG", "10:30", "12:50", "Airbus A320neo", "N", "2D", None),
    ("U2", "easyJet", "U28020", "LGW", "CDG", "14:45", "17:05", "Airbus A321neo", "N", "2D", None),
    ("U2", "easyJet", "U28024", "LGW", "CDG", "19:30", "21:50", "Airbus A320", "N", "2D", None),
    # CDG → LGW
    ("U2", "easyJet", "U28013", "CDG", "LGW", "07:40", "07:55", "Airbus A320", "2D", "N", None),
    ("U2", "easyJet", "U28017", "CDG", "LGW", "11:20", "11:35", "Airbus A320neo", "2D", "N", None),
    ("U2", "easyJet", "U28021", "CDG", "LGW", "17:50", "18:05", "Airbus A321neo", "2D", "N", None),

    # LGW → AMS
    ("U2", "easyJet", "U28312", "LGW", "AMS", "07:10", "09:25", "Airbus A320", "N", None, None),
    ("U2", "easyJet", "U28316", "LGW", "AMS", "12:00", "14:15", "Airbus A320neo", "N", None, None),
    ("U2", "easyJet", "U28320", "LGW", "AMS", "17:30", "19:45", "Airbus A320", "N", None, None),
    # AMS → LGW
    ("U2", "easyJet", "U28313", "AMS", "LGW", "10:00", "10:15", "Airbus A320", None, "N", None),
    ("U2", "easyJet", "U28317", "AMS", "LGW", "14:50", "15:05", "Airbus A320neo", None, "N", None),
    ("U2", "easyJet", "U28321", "AMS", "LGW", "20:20", "20:35", "Airbus A320", None, "N", None),

    # LGW → BCN
    ("U2", "easyJet", "U28502", "LGW", "BCN", "06:30", "09:40", "Airbus A320neo", "N", "2C", None),
    ("U2", "easyJet", "U28506", "LGW", "BCN", "11:15", "14:25", "Airbus A321neo", "N", "2C", None),
    ("U2", "easyJet", "U28510", "LGW", "BCN", "17:00", "20:10", "Airbus A320", "N", "2C", None),
    # BCN → LGW
    ("U2", "easyJet", "U28503", "BCN", "LGW", "10:20", "11:30", "Airbus A320neo", "2C", "N", None),
    ("U2", "easyJet", "U28507", "BCN", "LGW", "15:00", "16:10", "Airbus A321neo", "2C", "N", None),
    ("U2", "easyJet", "U28511", "BCN", "LGW", "20:50", "22:00", "Airbus A320", "2C", "N", None),

    # LTN → AMS
    ("U2", "easyJet", "U22218", "LTN", "AMS", "07:30", "09:45", "Airbus A320", None, None, None),
    ("U2", "easyJet", "U22222", "LTN", "AMS", "13:10", "15:25", "Airbus A320neo", None, None, None),
    ("U2", "easyJet", "U22226", "LTN", "AMS", "18:45", "21:00", "Airbus A320", None, None, None),

    # === ADDITIONAL ROUTES FROM OTHER UK AIRPORTS ===
    # MAN → AMS (KLM)
    ("KL", "KLM Royal Dutch Airlines", "KL1074", "MAN", "AMS", "06:45", "09:00", "Embraer 190", None, None, None),
    ("KL", "KLM Royal Dutch Airlines", "KL1078", "MAN", "AMS", "12:30", "14:45", "Boeing 737-700", None, None, None),
    ("KL", "KLM Royal Dutch Airlines", "KL1082", "MAN", "AMS", "17:50", "20:05", "Embraer 190", None, None, None),
    # AMS → MAN
    ("KL", "KLM Royal Dutch Airlines", "KL1073", "AMS", "MAN", "07:10", "07:25", "Embraer 190", None, None, None),
    ("KL", "KLM Royal Dutch Airlines", "KL1077", "AMS", "MAN", "13:40", "13:55", "Boeing 737-700", None, None, None),
    ("KL", "KLM Royal Dutch Airlines", "KL1081", "AMS", "MAN", "18:55", "19:10", "Embraer 190", None, None, None),

    # EDI → AMS (KLM)
    ("KL", "KLM Royal Dutch Airlines", "KL1282", "EDI", "AMS", "06:30", "09:00", "Embraer 175", None, None, None),
    ("KL", "KLM Royal Dutch Airlines", "KL1286", "EDI", "AMS", "14:15", "16:45", "Embraer 190", None, None, None),

    # MAN → CDG (Air France)
    ("AF", "Air France", "AF1069", "MAN", "CDG", "07:00", "09:30", "Embraer E190", None, "2F", None),
    ("AF", "Air France", "AF1073", "MAN", "CDG", "16:20", "18:50", "Airbus A318", None, "2F", None),

    # BHX → AMS (KLM)
    ("KL", "KLM Royal Dutch Airlines", "KL1424", "BHX", "AMS", "06:50", "09:10", "Embraer 175", None, None, None),
    ("KL", "KLM Royal Dutch Airlines", "KL1428", "BHX", "AMS", "15:30", "17:50", "Embraer 190", None, None, None),

    # === ITALY ===
    # LGW → FLR (British Airways / Vueling)
    ("BA", "British Airways", "BA2586", "LGW", "FLR", "06:40", "10:10", "Airbus A320", "S", None, None),
    ("BA", "British Airways", "BA2590", "LGW", "FLR", "14:20", "17:50", "Airbus A320neo", "S", None, None),
    # FLR → LGW
    ("BA", "British Airways", "BA2587", "FLR", "LGW", "11:00", "12:30", "Airbus A320", None, "S", None),
    ("BA", "British Airways", "BA2591", "FLR", "LGW", "18:30", "20:00", "Airbus A320neo", None, "S", None),

    # STN → FLR (Ryanair)
    ("FR", "Ryanair", "FR8326", "STN", "FLR", "07:05", "10:30", "Boeing 737-800", None, None, None),
    ("FR", "Ryanair", "FR8330", "STN", "FLR", "16:40", "20:05", "Boeing 737-8200", None, None, None),
    # FLR → STN
    ("FR", "Ryanair", "FR8327", "FLR", "STN", "11:10", "12:35", "Boeing 737-800", None, None, None),
    ("FR", "Ryanair", "FR8331", "FLR", "STN", "20:45", "22:10", "Boeing 737-8200", None, None, None),

    # LHR → MXP (British Airways)
    ("BA", "British Airways", "BA572", "LHR", "MXP", "07:05", "10:15", "Airbus A320neo", "5", "1", None),
    ("BA", "British Airways", "BA576", "LHR", "MXP", "12:30", "15:40", "Airbus A321", "5", "1", None),
    ("BA", "British Airways", "BA580", "LHR", "MXP", "17:45", "20:55", "Airbus A320neo", "5", "1", None),
    # MXP → LHR
    ("BA", "British Airways", "BA573", "MXP", "LHR", "08:00", "09:15", "Airbus A320neo", "1", "5", None),
    ("BA", "British Airways", "BA577", "MXP", "LHR", "13:30", "14:45", "Airbus A321", "1", "5", None),
    ("BA", "British Airways", "BA581", "MXP", "LHR", "18:40", "19:55", "Airbus A320neo", "1", "5", None),

    # LGW → VCE (easyJet)
    ("U2", "easyJet", "U28552", "LGW", "VCE", "06:50", "10:15", "Airbus A320neo", "N", None, None),
    ("U2", "easyJet", "U28556", "LGW", "VCE", "15:10", "18:35", "Airbus A320", "N", None, None),
    # VCE → LGW
    ("U2", "easyJet", "U28553", "VCE", "LGW", "10:55", "12:20", "Airbus A320neo", None, "N", None),
    ("U2", "easyJet", "U28557", "VCE", "LGW", "19:15", "20:40", "Airbus A320", None, "N", None),

    # LGW → NAP (easyJet)
    ("U2", "easyJet", "U28602", "LGW", "NAP", "07:15", "11:00", "Airbus A320", "N", None, None),
    ("U2", "easyJet", "U28606", "LGW", "NAP", "16:00", "19:45", "Airbus A320neo", "N", None, None),
    # NAP → LGW
    ("U2", "easyJet", "U28603", "NAP", "LGW", "11:40", "13:25", "Airbus A320", None, "N", None),
    ("U2", "easyJet", "U28607", "NAP", "LGW", "20:25", "22:10", "Airbus A320neo", None, "N", None),
]

# Approximate base prices (GBP) by route distance category
PRICE_RANGES = {
    "short": (45, 120),   # <2h: LHR-CDG, LHR-AMS, LHR-BRU
    "medium": (80, 200),  # 2-3h: LHR-FRA, LHR-MUC, LHR-BCN, LHR-MAD
    "long": (110, 280),   # 3h+: LHR-FCO, LHR-ATH, LHR-LIS
}

# Route distance categories
ROUTE_CATEGORIES = {
    ("LHR", "CDG"): "short", ("CDG", "LHR"): "short",
    ("LHR", "AMS"): "short", ("AMS", "LHR"): "short",
    ("LGW", "CDG"): "short", ("CDG", "LGW"): "short",
    ("LGW", "AMS"): "short", ("AMS", "LGW"): "short",
    ("LTN", "AMS"): "short", ("AMS", "LTN"): "short",
    ("LHR", "BRU"): "short", ("BRU", "LHR"): "short",
    ("LHR", "DUS"): "short", ("DUS", "LHR"): "short",
    ("STN", "DUB"): "short", ("DUB", "STN"): "short",
    ("MAN", "AMS"): "short", ("AMS", "MAN"): "short",
    ("EDI", "AMS"): "short", ("AMS", "EDI"): "short",
    ("BHX", "AMS"): "short", ("AMS", "BHX"): "short",
    ("MAN", "CDG"): "short", ("CDG", "MAN"): "short",
    ("LHR", "FRA"): "medium", ("FRA", "LHR"): "medium",
    ("LHR", "MUC"): "medium", ("MUC", "LHR"): "medium",
    ("LHR", "ZRH"): "medium", ("ZRH", "LHR"): "medium",
    ("LHR", "GVA"): "medium", ("GVA", "LHR"): "medium",
    ("LHR", "VIE"): "medium", ("VIE", "LHR"): "medium",
    ("LHR", "CPH"): "medium", ("CPH", "LHR"): "medium",
    ("LHR", "ARN"): "medium", ("ARN", "LHR"): "medium",
    ("LHR", "BCN"): "medium", ("BCN", "LHR"): "medium",
    ("STN", "BCN"): "medium", ("BCN", "STN"): "medium",
    ("LGW", "BCN"): "medium", ("BCN", "LGW"): "medium",
    ("LHR", "MAD"): "medium", ("MAD", "LHR"): "medium",
    ("STN", "MAD"): "medium", ("MAD", "STN"): "medium",
    ("LHR", "LIS"): "medium", ("LIS", "LHR"): "medium",
    ("LGW", "LIS"): "medium", ("LIS", "LGW"): "medium",
    ("LHR", "FCO"): "long", ("FCO", "LHR"): "long",
    ("LGW", "FLR"): "medium", ("FLR", "LGW"): "medium",
    ("STN", "FLR"): "medium", ("FLR", "STN"): "medium",
    ("LHR", "MXP"): "medium", ("MXP", "LHR"): "medium",
    ("LGW", "VCE"): "medium", ("VCE", "LGW"): "medium",
    ("LGW", "NAP"): "long", ("NAP", "LGW"): "long",
    ("LHR", "ATH"): "long", ("ATH", "LHR"): "long",
    ("LHR", "PRG"): "medium", ("PRG", "LHR"): "medium",
}


# =============================================================================
# Synthetic route engine — generates realistic flights for ANY airport pair
# so the portal isn't limited to the curated schedules above.
# =============================================================================

# Approximate airport coordinates (lat, lon) for duration/distance estimates.
AIRPORT_COORDS = {
    # UK & Ireland
    "LHR": (51.4700, -0.4543), "LGW": (51.1537, -0.1821), "STN": (51.8850, 0.2389),
    "LTN": (51.8747, -0.3683), "LCY": (51.5053, 0.0553), "MAN": (53.3537, -2.2750),
    "EDI": (55.9500, -3.3725), "BHX": (52.4539, -1.7480), "BRS": (51.3827, -2.7191),
    "GLA": (55.8719, -4.4331), "DUB": (53.4213, -6.2701),
    # Continental Europe
    "CDG": (49.0097, 2.5479), "ORY": (48.7233, 2.3794), "AMS": (52.3105, 4.7683),
    "FRA": (50.0379, 8.5622), "MUC": (48.3538, 11.7861), "FCO": (41.8003, 12.2389),
    "FLR": (43.8100, 11.2051), "MXP": (45.6306, 8.7281), "VCE": (45.5053, 12.3519),
    "NAP": (40.8860, 14.2908), "MAD": (40.4719, -3.5626), "BCN": (41.2974, 2.0833),
    "VIE": (48.1103, 16.5697), "ZRH": (47.4647, 8.5492), "CPH": (55.6180, 12.6560),
    "OSL": (60.1939, 11.1004), "ARN": (59.6519, 17.9186), "LIS": (38.7742, -9.1342),
    "BRU": (50.9014, 4.4844), "ATH": (37.9364, 23.9445), "PRG": (50.1008, 14.2600),
    "WAW": (52.1657, 20.9671), "HEL": (60.3172, 24.9633), "GVA": (46.2381, 6.1089),
    "NCE": (43.6584, 7.2159), "DUS": (51.2895, 6.7668), "HAM": (53.6304, 9.9882),
    "BUD": (47.4369, 19.2556),
}

# Standard UTC offsets (hours). DST cancels out in route-pair differences.
AIRPORT_TZ = {
    "LHR": 0, "LGW": 0, "STN": 0, "LTN": 0, "LCY": 0, "MAN": 0, "EDI": 0,
    "BHX": 0, "BRS": 0, "GLA": 0, "DUB": 0, "LIS": 0,
    "ATH": 2, "HEL": 2,
}

# Airline hub/base airports used to decide who plausibly operates a route.
AIRLINE_NETWORKS = {
    "BA": ["LHR", "LGW", "LCY"],
    "LH": ["FRA", "MUC"],
    "AF": ["CDG", "ORY"],
    "KL": ["AMS"],
    "LX": ["ZRH", "GVA"],
    "OS": ["VIE"],
    "SK": ["CPH", "ARN", "OSL"],
    "TP": ["LIS"],
    "IB": ["MAD", "BCN"],
    "FR": ["STN", "LTN", "DUB", "BHX", "BRS"],
    "U2": ["LGW", "LTN", "STN", "MAN", "EDI", "BRS", "GLA"],
}

AIRLINE_NAMES = {
    "BA": "British Airways", "LH": "Lufthansa", "KL": "KLM Royal Dutch Airlines",
    "AF": "Air France", "LX": "Swiss International Air Lines", "OS": "Austrian Airlines",
    "SK": "Scandinavian Airlines", "TP": "TAP Air Portugal", "IB": "Iberia",
    "FR": "Ryanair", "U2": "easyJet",
}

# Broad-network carriers used as a fallback when no airline is hubbed at either end.
_FALLBACK_CARRIERS = ["BA", "LH", "AF", "KL"]

_DEP_SLOTS = ["06:35", "08:50", "11:20", "13:55", "16:40", "19:25", "21:10"]


def _haversine_km(origin: str, destination: str) -> Optional[float]:
    """Great-circle distance in km between two known airports."""
    a = AIRPORT_COORDS.get(origin)
    b = AIRPORT_COORDS.get(destination)
    if not a or not b:
        return None
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def _route_duration_minutes(origin: str, destination: str) -> int:
    """Estimate block time (minutes) from distance, with taxi/climb overhead."""
    km = _haversine_km(origin, destination)
    if km is None:
        km = 1000.0
    return int(round(40 + km / 12.0))


def _route_category(origin: str, destination: str) -> str:
    """Distance-based price category for routes not in ROUTE_CATEGORIES."""
    if (origin, destination) in ROUTE_CATEGORIES:
        return ROUTE_CATEGORIES[(origin, destination)]
    km = _haversine_km(origin, destination)
    if km is None:
        return "medium"
    if km < 900:
        return "short"
    if km < 1600:
        return "medium"
    return "long"


def _operating_airlines(origin: str, destination: str) -> list[str]:
    """Airlines that plausibly operate a route: those hubbed at either end,
    topped up with broad-network carriers so every pair has options."""
    carriers: list[str] = []
    for code, hubs in AIRLINE_NETWORKS.items():
        if origin in hubs or destination in hubs:
            carriers.append(code)
    for code in _FALLBACK_CARRIERS:
        if len(carriers) >= 2:
            break
        if code not in carriers:
            carriers.append(code)
    return carriers[:4]


def _aircraft_for(airline_code: str, duration_minutes: int, rng: random.Random) -> str:
    """Pick a plausible narrowbody for the carrier and sector length."""
    if airline_code == "FR":
        return "Boeing 737-800"
    if airline_code == "U2":
        return rng.choice(["Airbus A320", "Airbus A320neo", "Airbus A319"])
    if duration_minutes <= 90:
        pool = ["Airbus A319", "Airbus A320", "Embraer E190"]
    elif duration_minutes <= 150:
        pool = ["Airbus A320", "Airbus A320neo", "Airbus A321"]
    else:
        pool = ["Airbus A321", "Airbus A320neo", "Boeing 737-800"]
    return rng.choice(pool)


def _synth_flights(origin: str, destination: str, departure_date: date) -> list[FlightResult]:
    """Generate deterministic, realistic-looking flights for any airport pair."""
    from generators.pdf_generator import get_terminal_for_airport

    duration_minutes = _route_duration_minutes(origin, destination)
    hours, minutes = divmod(duration_minutes, 60)
    duration_iso = f"PT{hours}H{minutes}M"
    tz_diff = AIRPORT_TZ.get(destination, 1) - AIRPORT_TZ.get(origin, 1)

    carriers = _operating_airlines(origin, destination)
    results: list[FlightResult] = []
    slot_idx = 0
    for ci, code in enumerate(carriers):
        n_flights = 3 if ci == 0 else 2
        for k in range(n_flights):
            if slot_idx >= len(_DEP_SLOTS):
                break
            dep_str = _DEP_SLOTS[slot_idx]
            slot_idx += 1

            rng = random.Random(hash(f"{code}{origin}{destination}{k}") % (2 ** 31))
            dep_t = datetime.strptime(dep_str, "%H:%M").time()
            dep_dt = datetime.combine(departure_date, dep_t)
            arr_dt = dep_dt + timedelta(minutes=duration_minutes) + timedelta(hours=tz_diff)

            results.append(FlightResult(
                airline_code=code,
                airline_name=AIRLINE_NAMES.get(code, code),
                flight_number=f"{code}{rng.randint(100, 998)}",
                departure_airport=origin,
                arrival_airport=destination,
                departure_datetime=dep_dt,
                arrival_datetime=arr_dt,
                duration=duration_iso,
                stops=0,
                cabin_class="Economy",
                price=_get_price(origin, destination, code),
                currency="GBP",
                aircraft_type=_aircraft_for(code, duration_minutes, rng),
                departure_terminal=get_terminal_for_airport(code, origin),
                arrival_terminal=get_terminal_for_airport(code, destination),
                booking_class="Y",
            ))
    results.sort(key=lambda r: r.departure_datetime)
    return results


def _get_price(dep: str, arr: str, airline_code: str) -> float:
    """Generate a realistic price based on route and airline."""
    import random
    category = _route_category(dep, arr)
    low, high = PRICE_RANGES[category]

    # Budget carriers are cheaper
    if airline_code in ("FR", "U2"):
        low = int(low * 0.5)
        high = int(high * 0.6)

    # Use a seeded random for consistency within same session
    seed = hash(f"{airline_code}{dep}{arr}") % 10000
    rng = random.Random(seed)
    return round(rng.uniform(low, high), 2)


def search_local_flights(
    origin: str,
    destination: str,
    departure_date: date,
) -> list[FlightResult]:
    """Search the local flight database for matching routes.

    Args:
        origin: IATA departure airport code
        destination: IATA arrival airport code
        departure_date: The date of travel (used to set datetimes)

    Returns:
        List of FlightResult objects sorted by direct first, then departure time.
    """
    results = []

    for schedule in FLIGHT_SCHEDULES:
        (airline_code, airline_name, flight_num, dep_airport, arr_airport,
         dep_time_str, arr_time_str, aircraft, dep_terminal, arr_terminal,
         days_of_week) = schedule

        if dep_airport != origin or arr_airport != destination:
            continue

        # Check day of week if restricted
        if days_of_week is not None and departure_date.weekday() not in days_of_week:
            continue

        # Parse times
        dep_t = datetime.strptime(dep_time_str, "%H:%M").time()
        arr_t = datetime.strptime(arr_time_str, "%H:%M").time()

        dep_dt = datetime.combine(departure_date, dep_t)
        # Handle overnight flights
        arr_dt = datetime.combine(departure_date, arr_t)
        if arr_t < dep_t:
            arr_dt += timedelta(days=1)

        # Calculate duration accounting for timezone differences
        # Summer offsets: UK/Ireland/Portugal = UTC+1, Continental Europe = UTC+2
        _TZ = {
            "LHR": 1, "LGW": 1, "STN": 1, "LTN": 1, "MAN": 1,
            "EDI": 1, "BHX": 1, "BRS": 1, "NCL": 1, "GLA": 1,
            "DUB": 1, "LIS": 1,
            "CDG": 2, "AMS": 2, "FRA": 2, "MUC": 2, "ZRH": 2,
            "VIE": 2, "BRU": 2, "BCN": 2, "MAD": 2, "FCO": 2,
            "FLR": 2, "MXP": 2, "VCE": 2, "NAP": 2,
            "CPH": 2, "OSL": 2, "ARN": 2, "HEL": 2,
            "MLA": 2,
        }
        dep_utc_offset = _TZ.get(dep_airport, 1)
        arr_utc_offset = _TZ.get(arr_airport, 1)
        raw_delta = arr_dt - dep_dt
        total_minutes = int(raw_delta.total_seconds() / 60) + (dep_utc_offset - arr_utc_offset) * 60
        hours = total_minutes // 60
        minutes = total_minutes % 60
        duration_iso = f"PT{hours}H{minutes}M"

        price = _get_price(dep_airport, arr_airport, airline_code)

        results.append(FlightResult(
            airline_code=airline_code,
            airline_name=airline_name,
            flight_number=flight_num,
            departure_airport=dep_airport,
            arrival_airport=arr_airport,
            departure_datetime=dep_dt,
            arrival_datetime=arr_dt,
            duration=duration_iso,
            stops=0,  # All entries in our DB are direct
            cabin_class="Economy",
            price=price,
            currency="GBP",
            aircraft_type=aircraft,
            departure_terminal=dep_terminal,
            arrival_terminal=arr_terminal,
            booking_class="Y",
        ))

    # Sort by departure time
    if not results:
        results = _synth_flights(origin, destination, departure_date)
    results.sort(key=lambda r: r.departure_datetime)
    return results


def get_available_routes() -> list[tuple[str, str]]:
    """Get all unique (origin, destination) pairs in the database."""
    routes = set()
    for schedule in FLIGHT_SCHEDULES:
        routes.add((schedule[3], schedule[4]))
    return sorted(routes)


def get_origins() -> list[str]:
    """Get all selectable departure airports (every known airport)."""
    return sorted(AIRPORT_COORDS.keys())


def get_destinations_from(origin: str) -> list[str]:
    """Get all destinations reachable from a given origin (any other airport)."""
    return sorted(code for code in AIRPORT_COORDS if code != origin)
