# Stealth Mode - Anti-Detection

This document explains how Medusa's stealth mode works to avoid bot detection.

## Overview

Stealth mode is **enabled by default** and uses a combination of Chrome flags and JavaScript injection to mask automation indicators. This prevents websites from detecting that the browser is being controlled by automation tools.

## How It Works

### 1. Chrome Command-Line Flags

When launching Chrome with `stealth_mode=True`, the following flags are added:

```python
--disable-blink-features=AutomationControlled  # Removes navigator.webdriver
--exclude-switches=enable-automation           # Disables automation extension
--disable-infobars                             # Removes "Chrome is being controlled" message
--disable-dev-shm-usage                        # Overcome limited resource problems
```

**Most Important:** `--disable-blink-features=AutomationControlled`
- This flag prevents Chrome from setting `navigator.webdriver = true`
- Without this, all websites can easily detect automation

### 2. Script Injection via CDP

After Chrome launches, stealth scripts are injected using `Page.addScriptToEvaluateOnNewDocument`. This ensures the scripts run **before** any page scripts, making detection nearly impossible.

**Properties Modified:**

#### navigator.webdriver ⚠️ CRITICAL
```javascript
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,  // MUST be undefined, NOT false!
});
```

**Why `undefined` instead of `false`?**
- Normal browsers have `navigator.webdriver === undefined`
- Setting it to `false` can actually flag you as suspicious
- Some detection scripts specifically check for `false` as a sign of tampering

**Double Protection:**
1. Chrome flag: `--disable-blink-features=AutomationControlled`
2. CDP injection: `Page.addScriptToEvaluateOnNewDocument` (runs before page scripts)
3. Immediate override: `Runtime.evaluate` (runs on current page as backup)

Even with the Chrome flag, some versions still leak `navigator.webdriver = true`, so script injection is MANDATORY.

#### navigator.plugins & navigator.mimeTypes
```javascript
// Real-looking plugins array
navigator.plugins = [
    "Chrome PDF Plugin",
    "Chrome PDF Viewer",
    "Native Client"
]
```
Headless browsers typically have 0 plugins. We add realistic plugins.

#### window.chrome.runtime
```javascript
window.chrome.runtime = {
    connect: undefined,
    sendMessage: undefined
}
```
Makes Chrome appear like a normal user browser, not automation.

#### Automation Properties Removal
```javascript
delete window.__webdriver_evaluate;
delete window.__selenium_evaluate;
delete window._Selenium_IDE_Recorder;
// ... and many more
```
Removes properties added by Selenium, Puppeteer, etc.

#### Hardware Fingerprinting
```javascript
navigator.hardwareConcurrency = 4;  // CPU cores
navigator.deviceMemory = 8;          // GB of RAM
```
Makes hardware specs look realistic and consistent.

#### Permissions API
```javascript
// Override permissions query to behave naturally
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({state: Notification.permission}) :
        originalQuery(parameters)
);
```

### 3. toString Protection
```javascript
Function.prototype.toString = function() {
    // Make our overrides look like native code
    return 'function get() { [native code] }';
};
```
Advanced detection scripts check `toString()` of overridden methods. We make them look native.

## Testing Stealth Mode

### Automated Test
```bash
python test_stealth.py
```

This will:
1. Launch Chrome with stealth mode
2. Navigate to bot detection test pages
3. Verify navigator properties
4. Show pass/fail results

**Expected Output:**
```
✓ navigator.webdriver: undefined (PASS)
✓ navigator.plugins.length: 3 (PASS)
✓ navigator.languages: ["en-US","en"] (PASS)
✓ window.chrome.runtime: exists (PASS)
✓ Automation flags: not detected (PASS)

RESULTS: 5/5 checks passed
✓ ALL CHECKS PASSED - Stealth mode is working!
```

**If you see `false` instead of `undefined`:**
```
⚠ navigator.webdriver: false (WARNING - should be undefined, not false)
  Some detection scripts may flag 'false' as suspicious
```
This means the Chrome flag worked but the CDP injection may have failed. Check that CDP is enabled.

### Manual Testing

Visit these bot detection websites:

1. **Sannysoft Bot Detector**
   - URL: https://bot.sannysoft.com/
   - Checks 20+ detection methods
   - Should show mostly green checkmarks

2. **Are You Headless?**
   - URL: https://arh.antoinevastel.com/bots/areyouheadless
   - Tests headless Chrome detection
   - Should say "You are NOT headless"

3. **Intoli Headless Test**
   - URL: https://intoli.com/blog/not-possible-to-block-chrome-headless/chrome-headless-test.html
   - Chrome headless detection test
   - Should show "Not headless"

4. **Fingerprint.com**
   - URL: https://fingerprint.com/demo/
   - Advanced fingerprinting demo
   - Should look like a normal browser

## What Gets Detected (Without Stealth Mode)

Without stealth mode, websites can easily detect automation:

| Property | Without Stealth | With Stealth |
|----------|----------------|--------------|
| `navigator.webdriver` | `true` ❌ | `undefined` ✅ |
| `navigator.plugins.length` | `0` ❌ | `3` ✅ |
| `window.__webdriver_evaluate` | exists ❌ | deleted ✅ |
| Chrome infobar | visible ❌ | hidden ✅ |
| `navigator.languages` | `["en"]` ⚠️ | `["en-US", "en"]` ✅ |

## Usage

### Enable Stealth Mode (Default)
```python
from browser import launch_chrome

# Stealth mode enabled by default
launch_chrome(url="https://example.com")

# Explicitly enable
launch_chrome(url="https://example.com", stealth_mode=True)
```

### Disable Stealth Mode
```python
# For testing/debugging only
launch_chrome(url="https://example.com", stealth_mode=False)
```

## Advanced Configuration

### Custom Stealth Scripts

You can add custom stealth scripts by modifying `stealth.py`:

```python
def get_stealth_scripts() -> list[str]:
    scripts = []

    # Add your custom script
    scripts.append("""
        // Your custom stealth logic here
        Object.defineProperty(navigator, 'vendor', {
            get: () => 'Google Inc.',
        });
    """)

    return scripts
```

### Verify Stealth is Working

```python
from stealth import verify_stealth

# After launching browser
results = verify_stealth(port=9222)

print(results)
# {
#     'webdriver': False,
#     'plugins_length': 3,
#     'languages': '["en-US","en"]',
#     'chrome_runtime': True,
#     'automation_flag': False
# }
```

## Limitations

### What Stealth Mode Can't Hide

1. **IP Address** - Use proxy for IP masking (configure in `config.json`)
2. **WebRTC Leaks** - Real IP may leak through WebRTC
3. **Canvas Fingerprinting** - Browser fingerprint remains consistent
4. **Behavioral Analysis** - Perfect mouse movements can be detected
5. **TLS Fingerprinting** - Chrome's TLS fingerprint is detectable

### Additional Protection

For maximum stealth:

1. **Use Proxies** (configured in `config.json`):
   ```json
   {
     "proxy": {
       "host": "proxy.example.com",
       "port": 8080,
       "username": "user",
       "password": "pass"
     }
   }
   ```

2. **Human-Like Behavior** (already implemented):
   - Random mouse movements with Bezier curves
   - Variable typing speeds
   - Random delays between actions

3. **Rotate User Agents** (not currently implemented):
   ```python
   # TODO: Add user-agent rotation
   args.append("--user-agent=Mozilla/5.0 ...")
   ```

4. **Canvas/WebGL Noise** (not currently implemented):
   - Add random noise to canvas fingerprint
   - Randomize WebGL parameters

## Troubleshooting

### Stealth Scripts Not Injecting

**Problem:** `navigator.webdriver` is still `true`

**Solutions:**
1. Check CDP is available: `redis-cli ping`
2. Ensure Chrome launched with `--remote-debugging-port=9222`
3. Check logs for "Stealth scripts injected successfully"

### Detection Still Occurring

**Problem:** Website still detects automation

**Check:**
1. Run `python test_stealth.py` to verify
2. Check browser console for errors
3. Website may use advanced detection (IP, behavior, fingerprinting)

**Advanced Sites:**
- Some sites use server-side detection (IP reputation, request patterns)
- Use residential proxies for IP masking
- Add more random delays between actions

### Browser Crashes

**Problem:** Chrome crashes after stealth injection

**Solution:**
- Disable stealth mode temporarily: `stealth_mode=False`
- Check Chrome version compatibility
- Try updating Chrome to latest version

## Best Practices

1. **Always Use Stealth Mode** for production automation
2. **Test on Detection Sites** before deploying
3. **Combine with Proxies** for IP masking
4. **Use Human-Like Delays** between actions
5. **Rotate User Agents** periodically
6. **Monitor Detection** - websites update detection methods

## References

- [Chrome Automation Detection](https://antoinevastel.com/bot%20detection/2019/07/19/detecting-chrome-headless-v3.html)
- [Puppeteer Stealth Plugin](https://github.com/berstend/puppeteer-extra/tree/master/packages/puppeteer-extra-plugin-stealth)
- [Bot Detection Methods](https://bot.sannysoft.com/)
- [WebDriver Detection](https://w3c.github.io/webdriver/#dfn-webdriver-property)

## Security Note

This stealth mode is designed for **legitimate automation** use cases like:
- Automated testing
- Web scraping with permission
- Social media management
- Task automation

**Do not use** for:
- Bypassing security measures
- Fraudulent activities
- Terms of Service violations
- Illegal activities

Always respect website terms of service and robots.txt.
