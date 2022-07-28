DEFAULT_DATA = """
profile_short_name:
profile_designer:
profile_description:
profile_schema_version:1.7
emulation_mode:0
recommended_level:3.3
expect_fc:
expect_colrchange:
preheat_power:1050
preheat_nominal_temperature:240
preheat_min_power_offset:10
preheat_min_time:20
preheat_max_time:60
preheat_check_gradient_time:30
preheat_target_in_future:30
preheat_mode:5
preheat_end_detection_count:5
preheat_temperature_proximity:8.5
roast_required_power:1200
roast_min_desired_rate_of_rise:4.8
roast_target_in_future:25
roast_use_prediction_method:1
roast_target_timeshift:1
roast_end_by_time_ratio:0.33333
roast_PID_Kp:0.7172
roast_PID_Ki:0
roast_PID_Kd:3.55
roast_PID_min_i:0
roast_PID_max_i:0
roast_PID_iLimitApplyAtZero:1
roast_PID_differentialOnError:1
specific_heat_adj_upper_temperature_limit:180
specific_heat_adj_lower_temperature_limit:80
specific_heat_adj_multiplier_Kp:2.1
specific_heat_adj_multiplier_Kd:4
zone1_time_start:0
zone1_time_end:0
zone1_multiplier_Kp:1
zone1_multiplier_Kd:1
zone1_boost:0
zone2_time_start:0
zone2_time_end:0
zone2_multiplier_Kp:1
zone2_multiplier_Kd:1
zone2_boost:0
zone3_time_start:0
zone3_time_end:0
zone3_multiplier_Kp:1
zone3_multiplier_Kd:1
zone3_boost:0
corner1_time_start:0
corner1_time_end:0
cooldown_hi_speed:17000
cooldown_lo_speed:15000
cooldown_lo_temperature:100
roast_levels:205,215,222,227,231,235,241
roast_profile:0,20,0,0,17.2159,50.0498,60,110,38.3006,84.3821,80.5548,134.267,120,160.8,100.854,149.917,139.672,171.982,174.7,182.1,157.775,177.903,193.549,186.774,237.527,192.252,208.82,188.832,267.263,195.794,300,199.1,278.959,196.973,356.715,204.833,600,228.5,576.632,226.194,0,0
fan_profile:0,14700,0,0,18,14700,60,14700,42,14700,300,14700,540,13200,300,13200,558,13200,600,13200,582.003,13200,0,0
"""
DEFAULT_PREFERENCES = """
ambient_cutoff_reference:35
ambient_cutoff_probe:35
ambient_cutoff_difference:3.5
ambient_default_temperature:22.5
cooldown_end_temperature:40
cooldown_end_ror_1st:-1.5
cooldown_end_ror_b2b:-0.5
cooldown_slow_time:30
"""
SONOFRESCO_DEFAULT_DATA = """
profile_short_name:
profile_designer:
profile_description:
profile_schema_version:1.7
roast_levels:
emulation_mode:1
recommended_level:3
expect_fc:
expect_colrchange:
preheat_power:875
preheat_nominal_temperature:240
preheat_min_power_offset:10
preheat_min_time:20
preheat_max_time:50
preheat_check_gradient_time:30
preheat_target_in_future:15
preheat_mode:5
preheat_end_detection_count:5
preheat_temperature_proximity:8.5
roast_required_power:1200
roast_min_desired_rate_of_rise:2
roast_target_in_future:25
roast_use_prediction_method:0
roast_target_timeshift:2
roast_end_by_time_ratio:0
roast_PID_Kp:0.7172
roast_PID_Ki:0
roast_PID_Kd:3.55
roast_PID_min_i:0
roast_PID_max_i:0
roast_PID_iLimitApplyAtZero:1
roast_PID_differentialOnError:1
specific_heat_adj_upper_temperature_limit:180
specific_heat_adj_lower_temperature_limit:80
specific_heat_adj_multiplier_Kp:2.1
specific_heat_adj_multiplier_Kd:4
zone1_time_start:0
zone1_time_end:0
zone1_multiplier_Kp:1
zone1_multiplier_Kd:1
zone1_boost:0
zone2_time_start:0
zone2_time_end:0
zone2_multiplier_Kp:1
zone2_multiplier_Kd:1
zone2_boost:0
zone3_time_start:0
zone3_time_end:0
zone3_multiplier_Kp:1
zone3_multiplier_Kd:1
zone3_boost:0
corner1_time_start:0
corner1_time_end:0
cooldown_hi_speed:15000
cooldown_lo_speed:15000
cooldown_lo_temperature:100
roast_profile:
fan_profile:0,14700,0,0,18,14700,60,14700,42,14700,300,14700,540,13200,300,13200,558,13200,600,13200,582.003,13200,0,0
"""

SONOFRESCO_DEFAULT_XML = """
<root>
	<profile>
		<name>Sonofresco Default</name>
		<temperature>20.0,92.0,165.0,197.0,217.0,224.5,242.0,</temperature>
		<time>0,60,300,540,780,870,1080,</time>
		<notes>Coffee Type:

Roast Level:</notes>
		<roast>193.0,196.5,200.0,203.5,207.0,210.5,214.0,217.5,221.0,224.5,</roast>
	</profile>
</root>
"""
NUMBER_OF_ZONES = 3
NUMBER_OF_CORNERS = 1

EVENT_NAMES = ["colour_change","first_crack","first_crack_end","second_crack","second_crack_end","roast_end"]

aboutThisFileParameters = [
    'profile_short_name',
    'profile_designer',
    'profile_description'
]
preferences = [
    'ambient_cutoff_reference',
    'ambient_cutoff_probe',
    'ambient_cutoff_difference',
    'ambient_default_temperature',
    'cooldown_end_temperature',
    'cooldown_end_ror_1st',
    'cooldown_end_ror_b2b',
    'cooldown_slow_time'
]
notFoundInLog = [
    'profile_description'
]
optionalInLog = [
    'native_schema_version',
    'development_percent',
    'calibration_data',
    'back2back_count'
] + EVENT_NAMES
readOnly = [
    'profile_schema_version'
]
logFileName =[
    'log_file_name'
]
profileDataInLog = [
    'profile_short_name',
    'profile_designer',
    'profile_file_name',
    'profile_modified'
]    
notSavedInProfile = [
    'profile_file_name',
    'profile_modified',
    'native_schema_version',
    'roasting_level'
] + EVENT_NAMES + [
    'development_percent',
    'tasting_notes',
    'model',
    'firmware_version',
    'motor_hours',    
    'heater_hours',    
    'ambient_temperature',
    'mains_voltage',
    'heater_power_available',
    'power_factor',
    'density_factor',
    'reference_temperature',
    'back2back_count',
    'time_jump',
    'preheat_heater_percent',
    'calibration_data'
] + preferences
nonNumericData = [
    'profile_schema_version',
    'roast_levels'
]
zoneAndCornerTimes = [
    'zone1_time_start',
    'zone1_time_end',
    'zone2_time_start',
    'zone2_time_end',
    'zone3_time_start',
    'zone3_time_end',
    'corner1_time_start',
    'corner1_time_end'
]
timeInMinSec = [
    'time_jump',
    'preheat_min_time',
    'preheat_max_time',
    'preheat_check_gradient_time',
    'preheat_target_in_future',
    'roast_target_in_future',
    'roast_target_timeshift'
] + zoneAndCornerTimes + EVENT_NAMES
keepZeroParameters =[
    'expect_fc',
    'expect_colrchange',
]
temperatureParameters = keepZeroParameters + [
    'preheat_nominal_temperature',
    'specific_heat_adj_upper_temperature_limit',
    'specific_heat_adj_lower_temperature_limit',
    'cooldown_lo_temperature',

    'ambient_temperature',
    'reference_temperature',

    'ambient_cutoff_reference',
    'ambient_cutoff_probe',
    'ambient_default_temperature',
    'cooldown_end_temperature'
]
temperatureDeltas = [
    'preheat_temperature_proximity',
    'roast_min_desired_rate_of_rise',

    'ambient_cutoff_difference',
    'cooldown_end_ror_1st',
    'cooldown_end_ror_b2b'
]
notOnTabs = [
    'emulation_mode',
    'recommended_level',
    'expect_fc',
    'expect_colrchange'
]
zoneBoosts = [
    'zone1_boost',
    'zone2_boost',
    'zone3_boost'
]
settingGroups = {
    'phases':[
        'recommended_level',
        'expect_fc',
        'expect_colrchange'
    ],
    'zones':[
        'zone1_time_start',
        'zone1_time_end',
        'zone1_multiplier_Kp',
        'zone1_multiplier_Kd',
        'zone1_boost',
        'zone2_time_start',
        'zone2_time_end',
        'zone2_multiplier_Kp',
        'zone2_multiplier_Kd',
        'zone2_boost',
        'zone3_time_start',
        'zone3_time_end',
        'zone3_multiplier_Kp',
        'zone3_multiplier_Kd',
        'zone3_boost',
        'corner1_time_start',
        'corner1_time_end'
    ]
}
