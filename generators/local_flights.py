"""Local flight schedule database — real flight numbers and times, no API needed."""

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


def _get_price(dep: str, arr: str, airline_code: str) -> float:
    """Generate a realistic price based on route and airline."""
    import random
    category = ROUTE_CATEGORIES.get((dep, arr), "medium")
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
    results.sort(key=lambda r: r.departure_datetime)
    return results


def get_available_routes() -> list[tuple[str, str]]:
    """Get all unique (origin, destination) pairs in the database."""
    routes = set()
    for schedule in FLIGHT_SCHEDULES:
        routes.add((schedule[3], schedule[4]))
    return sorted(routes)


def get_origins() -> list[str]:
    """Get all unique departure airports."""
    return sorted(set(s[3] for s in FLIGHT_SCHEDULES))


def get_destinations_from(origin: str) -> list[str]:
    """Get all destinations reachable from a given origin."""
    return sorted(set(s[4] for s in FLIGHT_SCHEDULES if s[3] == origin))
