#!/bin/bash
for size in "256x256 icon.png" "512x512 icon@2x.png" "512x256 logo.png" "1024x512 logo@2x.png"; do
  set -- $size
  convert -background none -density 300 -resize $1 logo.svg $2
done