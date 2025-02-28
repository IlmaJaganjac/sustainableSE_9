---
author: Student1 First and Last Name, Student2, Marvin Blommestijn
title: "Energy Efficiency of Search Engines"
image: "../img/p1_measuring_software/gX_template/cover.png"
date: 22/02/2025
summary: |-
 
---

# Introduction

With search engines becoming an inseparable part of our daily digital routines, their environmental impact extends beyond the servers that power them. While mainstream discussions often spotlight the vast energy demands of server farms, a closer look reveals a hidden cost: every search query triggers energy-intensive processes on your personal device, either through the number of requests made or the content that the search engine loads for each of the query results. Just as sustainable software engineering has sparked debates on the energy efficiency of development tools, this post turns the focus to the user's side of the equation, specifically a developer's.

Popular search engines such as Google, Bing, and DuckDuckGo are now being evaluated not only for their performance but also for their energy footprints. In parallel, sustainability-driven alternatives like Ecosia—renowned for initiatives such as tree planting [1]—offer a new perspective on digital responsibility. Our analysis zeroes in on the energy consumed by your device—from the instant a query is typed until the results are rendered—capturing metrics like power draw and CPU load.

This investigation raises a pivotal question: How does energy consumption vary across different search engines from the user’s perspective? We hypothesize that platforms optimized with sustainability in mind could reduce the energy demands on individual devices, shifting the focus from large-scale infrastructure to everyday digital interactions. This is not about modifying browser settings or visual themes; it’s about measuring the real-world energy impact of each query. Specifically, from the prespective of a student and a developer, we implore you to think which search engine is the best to use so that our energy usage is at a minimal amount while we continue to access accurate, relevant, and timely information without compromising performance or usability.

In this blog post, we outline our rigorous experimental setup—employing controlled devices and precise energy measurement tools—to offer actionable insights into reducing your digital carbon footprint. Join us as we detail our methodology, unveil our findings, and explore the implications for greener software practices and sustainable digital habits.

# Methodology
### Experimental Overview
We compare 12 different search engines: Google[^google], Bing[^bing], Yahoo[^yahoo], DuckDuckGo[^duckduckgo], Brave Search[^brave], Ecosia[^ecosia], OceanHero[^oceanhero], Startpage[^startpage], Qwant[^qwant], Swisscows[^swisscows], Mojeek[^mojeek],You.com[^youcom]

---

### Research Question and Hypothesis

**Research Question**  
How does energy consumption vary across different search engines during common search activities?

**Hypothesis**  
Search engines optimized for sustainability (e.g., Ecosia) will consume less energy than mainstream alternatives (e.g., Google), and certain features (e.g., dark mode, minimalist UI) will reduce power consumption.

---

### Experiment Setup

#### Software and Hardware
- **Hardware**:
  - **Laptop**: Dell XPS 15 7590  
  - **CPU**: Intel Core i9-9980HK @ 2.40GHz  
  - **RAM**: 16GiB DDR4 @ 2667 MHz  
  - **GPU**: NVIDIA GeForce GTX 1650 Mobile / Max-Q, Intel UHD Graphics 630
  - **OS**: Ubuntu 24.04.2 LTS (linux)
  - **Battery**: DELL GPM0365  
  - **Wi-Fi**: Intel Wi-Fi 6 AX200  
  - **Power Supply**: Dell charger, 19.5V 7.7A  

- **Software**:  
  - **Python (v. 3.19)**: used to write the script to run the automated tests and log/analyze the results
  - **Selenium (v. 4.29.0)**: a python package used to simulate the (Chromium based) browser along with clicks and any realistic input a user would make
  - **EnergiBridge (v. 0.0.7)**: The energy profiler **EnergiBridge**[^energibrigde] is used to measure and log power consumption.  

#### Procedure

Prior to any measurements, the system is placed in a **Zen mode** by closing all applications and unnecessary background services, disabling notifications and removing additional hardware, minimizing CPU and disk activity. This setup minimizes external variables that could otherwise impact energy usage. A brief **warm-up** follows, introducing a CPU-intensive task such as calculating a Fibonacci seqeuence to bring the system to a consistent operating temperature to ensure more accurate energy measurements.

Under these conditions, **identical search queries** (for instance, “climate change effects”) are performed on each search engine from the prespective of the profile user we chose (a student developer). Based on the article[^developersearches] "The hidden insights in developers’ Google searches", the average developer makes around 16 searches a day, searching for a variety of information like how to use an API, troubleshoot or learn to use a new technology. Due to time constraints we run 1 query "angular route uib tab".

During this process, energy usage, CPU load, and other relevant performance metrics are recorded. To ensure reliability, the test is repeated **30** times and the order of search engines is randomized to avoid systematic bias. After doing a query with a search engine, we wait 10 seconds before continuing to let the CPU return to normal levels. In addition, a **1–2 minute rest interval** is observed between test iterations so the system can return to an idle state before the next measurement.

Throughout each iteration, **Energibridge** logs timestamps to mark the start and end of the test window, and all power samples within that interval are aggregated to determine the total energy (in Joules) consumed by the search operation. 

Finally, we employ statistical tests to measure the differences between all the engines and see if our data is valid (as in if they are normal) and if there is any statistical difference.

<!-- Insert description on preliminary results and discovery of cookie/automation time and why baseline was introduced -->
During the initial runs, we observed unexpected variations in the recorded energy consumption. After investigating potential sources of discrepancy, we identified two key factors affecting our measurements:

 1. Cookie and Automation Detection: Search engines often modify their behavior when automated scripts perform queries, sometimes loading additional elements, triggering bot detection mechanisms, or introducing CAPTCHAs. This introduces variability in response times and energy consumption.

 2. Baseline Measurement: To differentiate the energy cost of executing a search query from the inherent cost of simply loading the website, we measured the baseline time required to load the search engine's homepage without any user interaction. By subtracting this baseline from the total recorded energy, we ensure that our results reflect the actual energy cost of performing a search rather than simply loading the search engine.

# Results

## Analysis

- **Statistical Evaluation:**  
  Apply statistical tests (e.g., Shapiro- Wilk test, Welch’s t-test, Cohen’s D). Statistical significance. . Is data normal?

- **Performance Metrics:** - 
  - time energy etc energibridge data
  - Energy & Power
  - Energy delay product  

## Plots and Visualizations

- **Violin + Box Plots:**  
  
- **Histograms, density Plots:**  



# Discussion and Future Work

- **Interpretation of Results:**  
From the results, a clear distinction emerges between Google and the other search engines in terms of energy consumption and duration. Google consistently stands out as the search engine with the longest response time, highest energy delay product, and greatest total energy consumption. The bar graph measuring average duration per search engine shows that Google takes significantly longer to return results compared to alternatives like You.com and Swisscows, which have much lower response times. A possible explanation for this could be that Google's search results involve more background processes, such as retrieving personalized search suggestions, preloading results, or running additional scripts to enhance the user experience. In contrast, search engines with lower durations may have simpler or more lightweight implementations, leading to faster responses and reduced energy usage. Additionally, the scatter plots confirm that Google's queries tend to be positioned in the upper-right region of the graph, reinforcing the correlation between high response time and energy consumption.

Looking at power consumption trends, Swisscows exhibits the highest peaks in power usage over time, although Google remains the most dominant in overall energy expenditure. The variation in power usage between engines could be linked to differences in the way search engines handle rendering and data retrieval. Some engines may load a search page more efficiently by reducing unnecessary processes, while others might consume more power in short bursts. The energy delay product (EDP) boxplots further emphasize Google’s significant outlier behavior, showing extreme values across all weighting factors (w=1, w=2, w=3), while other search engines remain relatively low and uniform. This suggests that Google’s combination of longer response time and higher energy use results in an exponential increase in EDP, making it the least energy-efficient option among the tested engines. Bing also exhibits slightly elevated EDP values but is still considerably lower than Google.

The comparative percentage change analyses between search engines further highlight Google’s dominance in energy consumption. Google’s total energy usage is consistently much higher when compared to any other engine, particularly against lightweight alternatives such as You.com and Startpage. The violin plots, which display power and total energy distributions, confirm that most search engines have relatively consistent energy usage patterns, whereas Google shows a wider spread along the y-axis, indicating a broader range of energy consumption levels across different queries. Additionally, Google remains the only search engine present in the duration range beyond 15 seconds in the memory usage plot, suggesting that it continues background processing even after returning search results. This behavior may contribute to its prolonged energy footprint. Overall, the results indicate that while Google remains a dominant force in search performance, its energy efficiency is notably lower than that of its competitors, raising questions about the trade-off between enhanced search functionality and sustainable computing practices.

<!-- Insert paragraph on 'normal' results that Google is now in the middle -->

- **Limitations:**
One of the key limitations of this study is that it only considers the client-side energy consumption, meaning the power usage of the user's device while performing search queries. However, search engines rely on extensive backend infrastructure, including data centers, caching mechanisms, and network requests, which also contribute significantly to their overall energy footprint. Since this study does not have access to backend server energy consumption data, it presents only a partial view of the environmental impact of different search engines. Future research would benefit from incorporating end-to-end energy consumption analysis, including network energy usage and server-side power draw, to provide a more holistic comparison of search engine sustainability.

Another limitation is the controlled testing environment, which does not fully replicate real-world usage conditions. The experiment was conducted with a fixed set of developer-focused queries, a single test system, and under an isolated "Zen mode" to minimize background noise. However, in everyday scenarios, search engine energy consumption could be influenced by factors such as hardware variations, network conditions, browser configurations, and concurrent background processes. Additionally, packet loss and TCP retransmissions were reported during testing, requiring additional CPU work and increasing energy usage in some cases. Poor network conditions can introduce inconsistencies in energy consumption, making it difficult to isolate search engine efficiency from network-related inefficiencies. These external factors may cause differences in energy efficiency that this study does not account for, limiting the generalizability of the results to a broader audience.
  
- **Future Research:**  
Future research should explore a more comprehensive measurement approach that includes both client-side and server-side energy consumption. Collaborating with search engine providers or leveraging publicly available data on server energy usage could help assess the total environmental cost of search queries. Additionally, measuring the energy impact of different types of searches (e.g., text vs. image/video searches) and incorporating network-level energy consumption (such as data transfer between the user and the search engine) would provide a more complete understanding of search engine sustainability.

Another promising direction for future work is expanding the scope of testing across different user conditions. This could involve testing on a range of devices (laptops, desktops, smartphones), varying internet speeds, and different browser types to analyze how search engine energy consumption changes under diverse circumstances. In addition to this, exploring how search engine settings—such as enabling dark mode, reducing JavaScript execution, or using lightweight search alternatives—impact energy efficiency could offer actionable recommendations for reducing digital carbon footprints. Lastly, with the rise of AI-powered search engines like Perplexity AI or ChatGPT-based search tools, future studies should investigate whether AI-driven search assistance consumes more or less energy compared to traditional keyword-based search engines.

Another addition to one of the plots was temperature measurements. Temperature measurements were taken using a Mac laptop’s built-in thermal sensors, but the results were similar across search engines and did not contribute significantly to the analysis. Future research could explore longer-term trends or external factors to assess their impact on energy efficiency.

And finally, future work could explore the sustainability impact of cookies, as some search engines required a baseline measurement due to automation protection. Investigating how cookies influence energy consumption and whether they introduce inefficiencies could provide further insights into the hidden environmental costs of web tracking.

# Conclusion
This study highlights significant differences in energy consumption, response time, and efficiency across search engines, with Google standing out as the least energy-efficient due to its long response times and high energy delay product. In contrast, You.com and Swisscows emerged as the most efficient options, demonstrating both lower response times and reduced energy consumption. While some search engines optimized performance by minimizing background processes, variations in power usage suggest differences in how results are processed and displayed. The findings emphasize the trade-off between enhanced functionality and sustainability, raising questions about the environmental impact of widely used search engines. Although the analysis focused on client-side energy consumption, future research should incorporate backend infrastructure energy usage, as well as factors like network transmission, cookies, and long-term energy trends. Expanding the study to diverse hardware setups, internet conditions, and emerging AI-driven search engines could further enhance our understanding of digital sustainability.

<!-- Edit conclusion to also mention the 'normal' plots of Google -->

# Replication Package

For researchers interested in replicating this study, the complete replication package is available at our GitHub repository [^replication].

# References
[^replication]: [GitHub repository](https://github.com/IlmaJaganjac/sustainableSE_9/)
[^energibrigde]: [Energibridge repo](https://github.com/tdurieux/EnergiBridge)  
[^greenspector]:[Greenspector - Environmental impact of search engines apps](https://greenspector.com/en/search-engines/)  
[^google]: [Google](https://www.google.com)  
[^bing]: [Bing](https://www.bing.com)  
[^yahoo]: [Yahoo](https://www.yahoo.com)  
[^duckduckgo]: [DuckDuckGo](https://duckduckgo.com)  
[^brave]: [Brave Search](https://search.brave.com)  
[^ecosia]: [Ecosia](https://www.ecosia.org)  
[^oceanhero]: [OceanHero](https://oceanhero.today)  
[^startpage]: [Startpage](https://www.startpage.com)  
[^qwant]: [Qwant](https://www.qwant.com)  
[^swisscows]: [Swisscows](https://swisscows.com)  
[^mojeek]: [Mojeek](https://www.mojeek.com)  
[^metager]: [MetaGer](https://metager.org)  
[^youcom]: [You.com](https://you.com)  
[^perplexity]: [Perplexity AI](https://www.perplexity.ai)
[^developersearches]: [Developer Searches](https://medium.com/design-bootcamp/the-hidden-insights-in-developers-google-searches-47f05030cd2d)



