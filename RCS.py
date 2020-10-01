import sys
from os import listdir
from hashlib import sha256
from getpass import getpass
from pickle import load, dump
from time import time, strftime, localtime
from subprocess import run, TimeoutExpired
from os.path import exists, splitext, join, abspath


class Testcase:

    def __init__(self, idx, inp, out, ans, judged_at, runtime, status, remark):

        self._idx = idx
        self._status = status
        self._remark = remark
        self._judged_at = judged_at
        self._input = inp.decode()
        self._output = out.decode()
        self._answer = ans.decode()
        self._runtime = str(runtime)[:5]
        if len(self._runtime) < 5:
            self._runtime += '0'

    def display(self):

        print("| {:^4} | {:^30} | {:^3} ms | {}".format(
            self._idx,
            self._status,
            self._runtime,
            self._remark
        ),
            end="\r\n"
        )

    def reveal(self):

        compress = (lambda x: (x[:255] + ["", "..."][len(x) > 255]))
        print("\nTESTCASE #{}".format(self._idx))
        print("VERDICT: {}".format(self._status))
        print("RUNTIME: {} ms".format(self._runtime))
        print("JUDGED AT: {}".format(self._judged_at))
        print("\nINPUT:\n{}".format(compress(self._input)))
        print("\nOUTPUT:\n{}".format(compress(self._output)))
        print("\nJURY'S OUTPUT:\n{}".format(compress(self._answer)))
        print("\nRemark:\n{}".format(self._remark))


class Checker:

    def __init__(self, base_path):

        self._TIMELIMIT = 2000
        self._INBUILT_PASS = "1a79668eac4051a9128b81c116007d1b41ce17828d7722afc9746699f4e817b8"

        self._COMPILE_CMDS = {
            ".c": "gcc {} -o {} --std=c99 -lm",
            ".cpp": "g++ {} -o {} --std=c++17"
        }

        self._VERDICT_MAP = {
            1: "\033[1;32mACCEPTED\033[0m",
            2: "\033[1;31mWRONG_ANSWER\033[0m",
            3: "\033[1;33mTIME_LIMIT_EXCEEDED\033[0m",
            4: "\033[1;31mRUNTIME_ERROR\033[0m",
        }

        self._base_path = base_path
        if sys.argv[1] == "judge":
            if len(sys.argv) < 3:
                print("usage: RCS.py judge X.c")
                sys.exit(0)
            self._verify_password()
            if not exists(sys.argv[2]):
                files = []
                for file in listdir():
                    if splitext(file)[1] in self._COMPILE_CMDS:
                        files.append(file)
                temp = [" is", "s are"][len(files) > 1]
                files = ", ".join(files)
                print("Specified file doesn't exist\nCheckable file{} {}".format(temp, files))
            else:
                self._judge(sys.argv[2])
        elif sys.argv[1] == "reveal":
            if len(sys.argv) < 3:
                print("usage: RCS.py reveal X")
                sys.exit(0)
            self._verify_password()
            try:
                results_file = open("results.dat", "rb")
                pack = load(results_file)
                results_file.close()
            except FileNotFoundError:
                print("Judge atleast once before revealing")
                sys.exit(0)
            pack[int(sys.argv[2])].reveal()
        elif sys.argv[1] == "clean":
            run("rm results.dat")
            run("rm RCS.exe")
        else:
            print("usage: RCS.py judge X.c | reveal X | clean")

    def _read(self, fname):

        path_to_file = join(self._base_path, fname)
        input_file = open(path_to_file, "rb")
        req_input = input_file.read()
        input_file.close()
        return req_input

    def _verify_password(self):

        tries = 3
        while tries > 0:
            if self._INBUILT_PASS == sha256(getpass("enter passwd: ").encode()).hexdigest():
                return
            else:
                print("Incorrect password. [{} tr{} left]".format(tries-1, ["ies", "y"][tries == 2]))
            tries -= 1
        print("Three incorrect attempts detected. Please verify password and try again.")
        sys.exit(0)

    def _judge(self, fname):

        pack = []
        score = verdict = 0
        judged_at = remark = None
        stem, ext = splitext(fname)
        if ext not in self._COMPILE_CMDS:
            print("{} extension is not allowed.\nAvailable languages: C, C++".format(ext))
            sys.exit(0)
        testcases = max_score = len(listdir(join(self._base_path, "inputs")))
        command = self._COMPILE_CMDS[ext].format(fname, stem)
        process = run(command)

        if not process.returncode:
            for tno in range(testcases):
                try:
                    req_input = self._read(
                        "inputs/inp{}.txt".format(tno + 1)).strip()
                    req_output = self._read(
                        "outputs/out{}.txt".format(tno +1)).strip()
                    start, end = time(), None
                    process = run("./{}".format(stem),
                                  input=req_input,
                                  capture_output=True,
                                  timeout=self._TIMELIMIT/1000)
                    end = time()
                    if not process.returncode:
                        output = process.stdout.strip()
                        diff = (req_output == output)
                        verdict = (1 if diff else 2)
                        remark = ("OK" if diff else "WA")
                        score += int(diff)
                    else:
                        remark = "RTE"
                        verdict = 4
                except TimeoutExpired:
                    if end is None:
                        end = time()
                    output = b"<no output>"
                    verdict = 3
                    remark = "TLE"
                except FileNotFoundError:
                    print("unable to fetch necessary files")
                    sys.exit(0)
                finally:
                    judged_at = strftime('%I:%M:%S %p, %d-%b-%Y', localtime())

                runtime = round((end - start), 4)
                status = self._VERDICT_MAP[verdict]
                test = Testcase(idx=tno,
                                inp=req_input,
                                out=output,
                                ans=req_output,
                                judged_at=judged_at,
                                runtime=(end-start),
                                status=status,
                                remark=remark)

                if not tno:
                    print("\n+{}+".format('-'*39))
                    print("| {:^4} | {:^19} | {:^4}  | ".format("SNO", "VERDICT", "RUNTIME"))
                    print("+{}+".format('-'*39))
                    print("+{}+".format('-'*39))
                test.display()
                print("+{}+".format('-'*39))
                pack.append(test)

            results_file = open("results.dat", "wb")
            dump(pack, results_file)
            results_file.close()
            
            print("\t\t+{}+".format('-'*12))
            print("\t\t| SCORE: {}/{} |".format(score, max_score))
            print("\t\t+{}+".format('-'*12))
            if score == max_score:
                print("\t\t| {:^10} |".format("\033[1;32mWELL DONE!\033[0m"))
                print("\t\t+{}+".format('-'*12))
        else:
            print("\033[1;31mCOMPILATION_ERROR\033[0m",)


# main function
def main():
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = abspath(".")
    Checker(base_path=base_path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nQuitting Judge...\n")
