# Push metrics to Geckoboard

This was used Shop2market to monitor traffic of the past day with python and bash.
The metrics are pushed to Geckoboard api in the custom graph format (Highcharts)
The python script stores scraped metrics and pushed the complete dataset everyday.. Because thats how it worked at the time.

The bash script also updated a login message for users of the R-Development server. This saves them time if there purpose was to login and copy and paste greps.

This script ran every 2 hours for over 2 years and because of the python pickle format is only 100K large at the day of writing.

Here how the graph looked at the time of writing

![An example of data graphed with highcharts](example-graph.png?raw=true)
