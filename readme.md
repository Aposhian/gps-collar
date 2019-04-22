# gps-collar

## Objectives
For specific time intervals:
1. **Calculate distance traveled by GPS collar**
2. **Calculate the area in which the collar stays for a specific time interval**

## Dependencies
python 3.x, shapely

## Methods
The first task is to split the datapoints into time intervals. The number of intervals per day can be specified as a command line argument. In order to best segregate data from different intervals, for any two adjacent time intervals, there is a new datapoint interpolated between the two datapoints closest to the boundary. This new datapoint is then added as the last datapoint of one interval, and as the first datapoint of the next interval. If there are no datapoints for a given interval, then the day is thrown out entirely, so as to not skew the data comparing different times of day.

Here is the formula:
Let the datapoints be described as vectors with xy-coordinates and time value t `<x,y,t>`.
Let `[t1,t2]`,`[t2,t3]` be time intervals and let there be datapoints `a = <xa,ya,ta>` and `b = <xb,yb,tb>` where `t1 < ta < tb` and `t2 < tb < t3`.
The interpolated datapoint `m = <xm,ym,t2>` between `a` and `b` will be given by the following formula: `m = [(t2 - ta) / (tb - ta)] * <xb - xa, yb - ya> + <xa,ya>`
This can be thought of as calculating the proportion of the difference between the first point and the boundary time to the total time difference between the two points. Then this scalar is multiplied by the `<x,y>` vector that is the difference between the two points, and added to the first `<x,y>` vector.