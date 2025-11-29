#!/bin/bash
echo "🤖 REENDER Build Script"
echo "================================"

# Python modüllerini yükle
pip install -r requirements.txt

# Gerekli dizinleri oluştur
mkdir -p server projects temp static templates

echo "✅ Build tamamlandı!"
