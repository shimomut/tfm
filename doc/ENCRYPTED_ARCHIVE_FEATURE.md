# Password-Protected ZIP Archives

TFM can extract and browse ZIP archives that are protected with a password.
When a password is needed, TFM prompts for it in a masked field — typed
characters show as `•`, and the value can't be copied or cut from the field.

## Extracting a password-protected ZIP

1. Put the cursor on the encrypted `.zip` file and press the **Extract Archive**
   key (`U`).
2. Confirm the destination as usual.
3. TFM detects that the archive is encrypted and asks for its password.
4. Enter the password and press **Enter**. The archive is extracted into a
   subdirectory (named after the archive) in the other pane.

If the password is wrong, TFM says so and asks again — nothing is written to
disk until the password is confirmed correct, so a wrong password never leaves a
half-extracted folder behind. Press **Esc** to cancel.

## Viewing a file inside a password-protected ZIP

1. Press **Enter** on the `.zip` file to browse it as a virtual directory. The
   file list is readable without a password.
2. Open a file inside it (**Enter** or the **View** key `V`).
3. TFM asks for the archive's password the first time you open a file from it.
4. Enter the password. The file opens in the built-in viewer.

The password is remembered for the rest of the session, so you're only asked
once per archive. Extracting an archive and later browsing the *same* archive
share the remembered password.

## Supported encryption

- **Legacy ZipCrypto** (the "traditional PKWARE" encryption produced by
  `zip -e`, most OS "compress with password" tools, and many archivers) is fully
  supported.
- **AES encryption** (WinZip AES / `7z -mem=AES256`) is **not** supported — the
  Python runtime TFM builds on can't decrypt it. TFM detects this and shows a
  clear "AES-encrypted zips are not supported" message instead of failing with a
  cryptic error.

Only the ZIP format supports passwords here; TAR archives (`.tar`, `.tar.gz`,
`.tar.bz2`, `.tar.xz`) are not encrypted.

## Notes

- Passwords are held only in memory for the running session and are never
  written to disk or logged.
- Passwords are sent to the archive as UTF-8 bytes. Plain ASCII passwords (the
  vast majority) always work; a non-ASCII password created by a tool using a
  different encoding may not match.
