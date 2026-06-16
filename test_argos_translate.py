import argostranslate.translate

text = "SQM Reports Earnings for the Three Months Ended March 31, 2026"

translated = argostranslate.translate.translate(
    text,
    "en",
    "zh",
)

print(translated)