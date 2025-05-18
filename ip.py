import requests

# Cấu hình
asn = "AS16276"  # ASN của OVHCloud
token = "a1112d496db7f6"  # Token IPInfo của bạn
output_file = "ovh_ranges.txt"

# Gọi API
url = f"https://ipinfo.io/{asn}/json?token={token}"
response = requests.get(url)

# Xử lý kết quả
if response.status_code == 200:
    data = response.json()
    prefixes = data.get("prefixes", [])
    print(f"Found {len(prefixes)} IP ranges.")

    with open(output_file, "w") as f:
        for prefix in prefixes:
            netblock = prefix.get("netblock")
            if netblock:
                f.write(netblock + "\n")
                print(netblock)

    print(f"\n✅ Done. IP ranges saved to '{output_file}'")

else:
    print(f"❌ Failed to fetch ASN data: {response.status_code}")
    print(response.text)
