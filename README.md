---
author: Student1 first and last name, Student2, Student3
title: "Title of the template blog"
image: "../img/p1_measuring_software/gX_template/cover.png"
date: 03/03/2022
summary: |-
  abstract Lorem ipsum dolor sit amet, consectetur adipisicing elit,
  sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
  Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris
  nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in 
  reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
  pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
  culpa qui officia deserunt mollit anim id est laborum.
---

## Introduction

In today’s digital landscape, search engines are an indispensable part of our everyday lives—but their energy consumption is a hidden cost with significant environmental implications. While much of the discussion around energy usage focuses on massive data centers and server farms, this blog post shifts the spotlight to the user’s perspective. Every time you type a query, your device—be it a laptop, smartphone, or tablet—engages in a series of energy-intensive processes that remain largely invisible. Our goal is to quantify and understand the energy consumed on your device with each search query.

This exploration delves into the energy efficiency of various search engines during everyday search activities. We compare mainstream options like Google, Bing, and DuckDuckGo with sustainability-oriented alternatives such as Ecosia, which champions eco-friendly practices like tree planting. Importantly, our measurements focus solely on the energy cost experienced by the user when initiating a search query—capturing the power draw, CPU load, and network activity that occur from the moment the query is entered until the results are rendered on your screen.

Driven by the question, How does energy consumption vary across different search engines from the user's perspective?, we hypothesize that search engines optimized for sustainability may offer lower energy usage on end-user devices compared to conventional platforms. This is not about tweaking browser settings or interface themes; instead, it is about measuring the real-world impact of a single queryo or a number of them (until the user extract the required information from them) on the energy footprint of your device.

By employing a rigorous experimental setup with controlled devices and precise energy measurement tools, this study offers actionable insights into reducing the digital carbon footprint at the individual level. Join us as we unpack our methodology, reveal our findings, and discuss what these results mean for greener software practices and sustainable digital habits.

---
## Methodology
Our experimental approach is both methodical and systematic, designed to ensure reproducibility and minimize external variability. Here’s a detailed breakdown of our methodology:

1. Zen Mode Setup
   
  Before any measurements begin, the system is prepared in a "Zen Mode" environment. This involves:
  - Closing all unnecessary applications and services: To eliminate interference from background tasks.
  - Disabling notifications: Ensuring no pop-ups or system alerts affect performance.
  - Restricting hardware usage: Only the essential hardware is connected (e.g., disconnecting external devices like USB drives or external displays) and using a stable, wired network connection to maintain consistent power consumption levels.

2. System Warm-Up

  To stabilize the hardware’s operating conditions, a Python script executes a Fibonacci sequence algorithm before the actual test begins. This “warm-up” phase ensures that:
  - CPU and hardware components reach an optimal operating temperature: Reducing initial fluctuations in power consumption.
  - Measurements reflect steady-state performance: Providing a reliable baseline for the subsequent energy measurements.

3. Energy Measurement with Energibridge

  For precise energy consumption data, we employ the Energibridge tool. Energibridge directly interfaces with hardware power monitors to record:
  - Energy consumption (in Watts)
  - CPU load
  - Network data transfer (pretty sure we don't measure this but ill leave it here cuz i might try to add it)

  By automating these measurements, Energibridge ensures that data is collected consistently and accurately during each test session.

4. User Profile and Search Task Automation

  A predefined user profile is central to our experiment:
  - Specific interactions: The profile outlines detailed steps, including specific search queries, clicks, and other interactions across various search engines.
  - Multiple repetitions: Each search task is executed repeatedly (with the order of tasks shuffled) to capture robust data and reduce the impact of transient external factors.

5. Systematic Data Collection

  Every phase of the experiment—from system warm-up to executing the search tasks—is carefully documented:
  - Hardware and software configurations: Detailed logs of system settings, browser versions, and ambient conditions are maintained.
  - Data reproducibility: The strict adherence to protocol ensures that the collected energy consumption data can be reliably compared across different search engines and settings.

  This type of methodology enables us to derive meaningful insights into the energy efficiency of search engines while maintaining high experimental rigor.

---
## Unbiased Energy Data ⚖️

There are a few things that need to be considered to minimise the bias of the energy measurements. Below, I pinpoint the most important strategies to minimise the impact of these biases when collecting the data.

### Zen mode 🧘🏾‍♀️

The first thing we need to make sure of is that the only thing running in our system is the software we want to measure. Unfortunately, this is impossible in practice – our system will always have other tasks and things that it will run at the same time. Still, we must at least minimise all these competing tasks:

- all applications should be closed, notifications should be turned off;
- only the required hardware should be connected (avoid USB drives, external disks, external displays, etc.);
- turn off notifications;
- remove any unnecessary services running in the background (e.g., web server, file sharing, etc.);
- if you do not need an internet or intranet connection, switch off your network;
- prefer cable over wireless – the energy consumption from a cable connection is more stable than from a wireless connection.

### Freeze your settings 🥶

It is not possible to shut off the unnecessary things that run in our system. Still, we need to at least make sure that they will behave the same across all sets of experiments. Thus, we must fix and report some configuration settings. One good example is the brightness and resolution of your screen – report the exact value and make sure it stays the same throughout the experiment. Another common mistake is to keep the automatic brightness adjustment on – this is, for example, an awful source of errors when measuring energy efficiency in mobile apps.

---

### 

Nevertheless, using statistical metrics to measure effect size is not enough – there should be a discussion of the **practical effect size**. More important than demonstrating that we came up with a new version that is more energy efficient, you need to demonstrate that the benefits will actually be reflected in the overall energy efficiency of normal usage of the software. For example, imagine that the results show that a given energy improvement was only able to save one joule of energy throughout a whole day of intensive usage of your cloud software. This perspective can hardly be captured by classic effect-size measures. The statistical approach to effect size (e.g., mean difference, Cohen's-*d*, and so on) is agnostic of the context of the problem at hand.
