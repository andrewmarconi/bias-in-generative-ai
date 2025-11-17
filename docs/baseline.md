# Baseline Reference for Parity Benchmark

This baseline provides reference distributions for demographic parity checks in generated images. See config/baseline.yaml for machine-readable baselines used by the analytics code. The intent is to enable quantitative parity benchmarking against the US and global population distributions described in this document.

Original Baseline Data:

## US National Proportions

### Gender Distribution
The United States has a fairly balanced gender distribution with a slight female majority. As of 2024-2025, females comprise **50.5%** of the population (167.84 million) while males account for **49.5%** (164.55 million). This translates to a gender ratio of 98 males per 100 females. The U.S. has maintained more females than males since 1946.[1][2][3]

### Age Distribution
The U.S. population age structure breaks down into three primary cohorts:[4][5]

 - **Under 18 years:** 22.16% (approximately 73.6 million children)
 - **18-64 years (working age):** 61.0% (approximately 202.8 million adults)
 - **65 years and older:** 16.84% (approximately 56.0 million seniors)

The median age in the United States reached **39.1 years** as of July 2024, increasing by 0.6 years since April 2020. The largest single age group is 30-34 years, representing 6.94% of the population (23.06 million people).[6][4]

### Race and Ethnicity Distribution
The U.S. racial and ethnic composition for 2024-2025 shows:[7][8][9]

 - **White (Non-Hispanic):** 58.2-63.44% (approximately 193-210 million)
 - **Hispanic or Latino (any race):** 18.5-19.1% (approximately 63 million)
 - **Black or African American:** 12.2-12.36% (approximately 41-46 million)
 - **Asian:** 5.6-5.82% (approximately 19 million)
 - **Two or more races (multiracial):** 10.71% (approximately 35.6 million)
 - **American Indian/Alaska Native:** 0.7-0.88% (approximately 2.9 million)
 - **Native Hawaiian/Pacific Islander:** 0.19-0.2% (approximately 629,000)

The U.S. has become increasingly diverse, with the White population's share decreasing from 69.1% in 2002 to 59.2% in 2022, while the Hispanic/Latino population grew from 13.3% to 19.1% over the same period.[10][11]

---

## Global Proportions

### Gender Distribution
Globally, the population shows a slight male majority. As of 2024 there are approximately **4.09 billion males (50.6%)** and **4.05 billion females (49.4%)** among the world's 8.1 billion people. This translates to a global sex ratio of approximately **101 males per 100 females**.[12][13][14]

The sex ratio varies by age: it's 1.05 males per female at birth, 1.05 for those under 15, 1.03 for ages 15-64, and 0.81 for those over 65. The UN projects that gender parity will be achieved globally by 2050, with females eventually outnumbering males after that point.[3][12]

### Age Distribution
The global age structure for 2024 shows:[15][16][17]

 - **Under 15 years:** Approximately 25% (around 2 billion children)
 - **15-64 years (working age):** Approximately 65% (around 5.3 billion adults)
 - **65 years and older:** Approximately 10% (around 800 million seniors)

The global median age is **30.9 years** as of 2025, significantly younger than the U.S. median. However, the world is aging rapidly—the number of people aged 60 and older is projected to increase from 1.1 billion in 2023 to 1.4 billion by 2030. By the late 2070s, those 65 and older globally are projected to reach 2.2 billion, surpassing the number of children under 18.[16][18][19]

### Race and Ethnicity Distribution
Global racial/ethnic demographics are more challenging to measure uniformly, but approximate distributions include:[20]

 - **Asian (primarily East Asian, South Asian, Southeast Asian):** Approximately 60% (around 4.8 billion people)
   - Han Chinese: ~1.2 billion
 - **Black/African:** Approximately 14% (around 1.1-1.4 billion people, including diaspora)
 - **White/Caucasian:** Approximately 10-12% (around 800 million-1 billion people)
 - **Native/Indigenous peoples:** Approximately 5-6.5%
 - **Mixed/Other:** Approximately 10%

Regional population distribution shows that Asia dominates with over 60% of global population, followed by Africa at approximately 14.5%, Europe and North America combined at 14.1%, and other regions comprising smaller shares.[21]

***

### Key Comparisons

When comparing your AI image generation results to these demographic baselines:

 - **U.S. baseline for race/ethnicity:** Your AI generated 0% White, 28% Asian, and 3% Black—dramatically different from U.S. proportions of ~60% White, ~6% Asian, and ~12% Black.
 - **Global baseline for race/ethnicity:** Your results show overrepresentation of Asian (28% vs. expected 60% if truly global) and severe underrepresentation of Black (3% vs. 14% globally).

The high proportion of "unclear" classifications (69%) in your data makes direct comparison challenging, but the identifiable categories reveal significant deviations from both U.S. and global demographic distributionsns.
