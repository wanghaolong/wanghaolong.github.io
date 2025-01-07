#!/bin/bash

for img in image*.png; do
    echo "Processing $img..."
    echo "=== Content of $img ===" > "${img%.png}.txt"
    tesseract "$img" stdout -l chi_sim+eng >> "${img%.png}.txt"
done
