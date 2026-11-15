#!/usr/bin/env python3
"""Configure a persistent upload key from GitHub Actions repository secrets."""
from pathlib import Path
import base64
import os

root = Path(os.environ['PROJECT_DIR'])
gradle = root / 'app/build.gradle.kts'
encoded = os.environ.get('SAITENWERK_KEYSTORE_BASE64', '').strip()
password = os.environ.get('SAITENWERK_KEYSTORE_PASSWORD', '').strip()
alias = os.environ.get('SAITENWERK_KEY_ALIAS', '').strip()
if not encoded or not password or not alias:
    raise SystemExit('FEHLER: Repository-Secrets SAITENWERK_KEYSTORE_BASE64, SAITENWERK_KEYSTORE_PASSWORD und SAITENWERK_KEY_ALIAS müssen gesetzt sein.')
try:
    data = base64.b64decode(encoded, validate=True)
except Exception as exc:
    raise SystemExit(f'FEHLER: SAITENWERK_KEYSTORE_BASE64 ist ungültig: {exc}')
if len(data) < 1024:
    raise SystemExit('FEHLER: Der dekodierte Signaturschlüssel ist unerwartet klein.')
key_file = root / 'saitenwerk-upload.jks'
key_file.write_bytes(data)

s = gradle.read_text(encoding='utf-8')
if 'create("saitenwerkUpload")' not in s:
    anchor = '    compileOptions {'
    block = '''    signingConfigs {
        create("saitenwerkUpload") {
            storeFile = rootProject.file("saitenwerk-upload.jks")
            storePassword = System.getenv("SAITENWERK_KEYSTORE_PASSWORD")
            keyAlias = System.getenv("SAITENWERK_KEY_ALIAS")
            keyPassword = System.getenv("SAITENWERK_KEYSTORE_PASSWORD")
        }
    }
    buildTypes {
        getByName("debug") {
            signingConfig = signingConfigs.getByName("saitenwerkUpload")
        }
    }

'''
    if anchor not in s:
        raise SystemExit('FEHLER: Gradle-Android-Konfigurationsanker nicht gefunden.')
    s = s.replace(anchor, block + anchor, 1)
    gradle.write_text(s, encoding='utf-8')
print('STABLE APK SIGNING CHECK: PASS')
print('Persistent signing key loaded from GitHub Actions secrets.')
