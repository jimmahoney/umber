"""
 testing subprocess
"""
import subprocess

for args in (['ls', '-al'], ['foo', '-bar'], ['ls', '-bad']):
    print()
    try:
        print(f"  run {args}")
        result = subprocess.run(args,
                                capture_output = True, # in result.stdout etc
                                text = True,           # strings not streams
                                check = True,
                                timeout = 1.0,         # in seconds
        )
        print( "  -- result --")
        print(f"  type(result) = {type(result)}")
        print(result)
        print(result.stdout)
    except Exception as e:
        # from docs.python.org/3/library/subprocess.html :
        #   * Trying to execute a non-existant file gives OSError.
        #   * Sending invalid args gives ValueError.
        #   * SubprocessError of various sorts (timeout, ...)
        #      .CalledProcessError if non-zero return code and check=True
        #      .TimeoutExpired if process takes too long
        print( "  -- exception thrown -- ")
        print(f"  type = {type(e)}")
        print(f"  args = {e.args}")
        print(f"  {e}")
print("Done.")
