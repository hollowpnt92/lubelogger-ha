#!/bin/bash
# Run this script on your Home Assistant instance to test the integration

echo "=== Testing LubeLogger Integration ==="
echo ""

INTEGRATION_DIR="/config/custom_components/lubelogger"

echo "1. Checking files exist..."
REQUIRED_FILES=("__init__.py" "manifest.json" "config_flow.py" "sensor.py" "client.py" "coordinator.py" "const.py" "strings.json")
MISSING_FILES=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$INTEGRATION_DIR/$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file MISSING"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    echo "ERROR: Missing files!"
    exit 1
fi

echo ""
echo "2. Checking manifest.json syntax..."
python3 -m json.tool "$INTEGRATION_DIR/manifest.json" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ manifest.json is valid JSON"
    echo "   Domain: $(python3 -c "import json; print(json.load(open('$INTEGRATION_DIR/manifest.json'))['domain'])")"
else
    echo "   ✗ manifest.json is INVALID"
    exit 1
fi

echo ""
echo "3. Checking Python syntax..."
for pyfile in "$INTEGRATION_DIR"/*.py; do
    if python3 -m py_compile "$pyfile" 2>/dev/null; then
        echo "   ✓ $(basename $pyfile) syntax OK"
    else
        echo "   ✗ $(basename $pyfile) has syntax errors:"
        python3 -m py_compile "$pyfile" 2>&1
        exit 1
    fi
done

echo ""
echo "4. Checking file permissions..."
if [ -r "$INTEGRATION_DIR" ] && [ -x "$INTEGRATION_DIR" ]; then
    echo "   ✓ Directory is readable and executable"
else
    echo "   ✗ Directory permissions issue"
fi

echo ""
echo "=== All checks passed! ==="
echo ""
echo "Next steps:"
echo "1. Restart Home Assistant completely"
echo "2. Check logs: ha core logs | grep -i lube"
echo "3. Try adding the integration in Settings → Devices & Services"

