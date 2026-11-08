Daily Sea Surface Temperatures

Term: from January 1st, 1982 to latest
Area: 89.875S - 89.875N, 0.125E - 359.875E, 0.25 degree x 0.25 degree
Method: Merged satellite and in-situ data Global Daily Sea Surface Temperature (MGDSST)

Explanation:                                                          
The MGDSST is analyzed based on SSTs derived from satellite's infrared sensors, microwave sensors, and in-situ SST (from buoys, floats, and ships). 

The NOAA/AVHRR High Resolution Picture Transmission (HRPT) data of the area adjacent to Japan were received and processed at the Meteorological Satellite Center of JMA. 
NOAA/AVHRR and MetOp/AVHRR Global Area Coverage (GAC) data and NPP/VIIRS and NOAA/VIIRS Level3 data are provided by National Oceanic and Atmospheric Administration, USA. AQUA/AMSR-E, Coriolis/WINDSAT, and GCOM-W/AMSR-2 data are provided by the Japan Aerospace Exploration Agency (JAXA). 
In-situ SSTs are collected at JMA via GTS and the Internet, and those are used for correction of biases in satellite SSTs

In the reanalysis data, SSTs under sea ice area are determined according to the statistical relation between sea-ice concentration and SST. 
The lowest SST is -1.8 degree Celsius where the sea-ice concentration is 100%.

Data Format:
One data file consists of 721 records, one header record and 720 data records from north to south. 
The header record contains the year, month, and day in four digits each from the left. 
Each data record includes 1440 grid point values and each value is written in three digits from west to east, 
with unit in 0.1 degree Celsius. 
That is, the first value of the first data record is for the grid centered at 89.875N and 0.125E, 
and the last value of the last data record is for that at 89.875S and 359.875E, respectively. 
'888' denotes the region of sea ice only in real time data, and '999' the region of land and the value cannot be determined. 

References:
Kurihara, Y., T. Sakurai, and T. Kuragano (2006): 
Global daily sea surface temperature analysis using data from satellite microwave radiometer, 
satellite infrared radiometer and in-situ observations. Weather Service Bulletin, 73, Special issue, s1-s18 (in Japanese).

For further information, please contact to administrator of the Regional Real Time Data Base at neargoos@climar.kishou.go.jp.
