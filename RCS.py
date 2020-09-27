from pickle import load, dump
from sys import argv, exit
from time import time, sleep, strftime, localtime
from subprocess import run, check_output, TimeoutExpired
from os.path import exists, splitext
from getpass import getpass
from os import listdir
from hashlib import sha256


class Testcase:

    def __init__(self, idx, inp, out, ans, judged_at, runtime, status, remark):

        self.idx = idx
        self.status = status
        self.remark = remark
        self.judged_at = judged_at
        self.input = inp.decode()
        self.output = out.decode()
        self.answer = ans.decode()
        self.runtime = str(runtime)[:5]
        if len(self.runtime) < 5:
            self.runtime += '0'

    def display(self):

        print("| {:^4} | {:^30} | {:^3} ms | {}".format(
            self.idx,
            self.status,
            self.runtime,
            self.remark
        ),
            end="\r\n"
        )

    def reveal(self):

        compress = (lambda x: (x[:255] + ["", "..."][len(x) > 255]))
        print("\nTESTCASE #{}".format(self.idx))
        print("VERDICT: {}".format(self.status))
        print("RUNTIME: {} ms".format(self.runtime))
        print("JUDGED AT: {}".format(self.judged_at))
        print("\nINPUT:\n{}".format(compress(self.input)))
        print("\nOUTPUT:\n{}".format(compress(self.output)))
        print("\nJURY'S OUTPUT:\n{}".format(compress(self.answer)))
        print("\nRemark:\n{}".format(self.remark))


class Checker:

    def __init__(self):

        self.TIMELIMIT = 2000
        self.INBUILT_PASS = "friday"

        self.COMPILE_CMDS = {
            ".c": "gcc {} -o {} --std=c99 -lm",
            ".cpp": "g++ {} -o {} --std=c++17"
        }

        self.VERDICT_MAP = {
            1: "\033[1;32mACCEPTED\033[0m",
            2: "\033[1;31mWRONG_ANSWER\033[0m",
            3: "\033[1;33mTIME_LIMIT_EXCEEDED\033[0m",
            4: "\033[1;31mRUNTIME_ERROR\033[0m",
        }

        if argv[1] == "set_pass":
            if self.INBUILT_PASS == getpass("enter inbuilt passwd: "):
                self._set_pass(getpass("enter new passwd: "))
            else:
                print("Incorrect password. Please try again.")
        elif argv[1] == "judge":
            if len(argv) < 3:
                print("usage: RCS.py judge X.c")
                exit(0)
            passwd = getpass("enter current passwd: ")
            if self._get_pass() == sha256(passwd.encode()).hexdigest():
                self._judge(argv[2])
            else:
                print("Incorrect password. Please try again.")
        elif argv[1] == "reveal":
            if len(argv) < 3:
                print("usage: RCS.py reveal X")
                exit(0)
            with open("results.dat", "rb") as results_file:
                pack = load(results_file)
                results_file.close()
            pack[int(argv[2])].reveal()
        elif argv[1] == "clean":
            self._clean()
        else:
            print("usage: RCS.py set_pass | judge X.c | reveal X | clean")

    def _get_pass(self):

        if not exists("pass.dat"):
            raise Exception("password file not found!")
        with open("pass.dat", "rb") as pass_file:
            password = load(pass_file)
            pass_file.close()
        return password

    def _set_pass(self, new_pass):

        with open("pass.dat", "wb") as pass_file:
            new_pass_hash = sha256(new_pass.encode()).hexdigest()
            dump(new_pass_hash, pass_file)
            pass_file.close()
        print("password updated!")

    def _read(self, fname):

        with open(fname, "rb") as input_file:
            req_input = input_file.read()
            input_file.close()
        return req_input

    def _clean(self):

        run("rm -rf inputs")
        run("rm -rf outputs")
        run("rm RCS.py")
        run("rm *.dat")

    def _judge(self, fname):

        pack = []
        score = verdict = 0
        judged_at = remark = None
        stem, ext = splitext(fname)
        if ext not in self.COMPILE_CMDS:
            print("{} extension is not allowed.\nAvailable languages: C, C++".format(ext))
            exit(0)
        testcases = max_score = len(listdir("inputs"))
        command = self.COMPILE_CMDS[ext].format(fname, stem)
        process = run(command)

        if process.returncode == 0:
            for i in range(testcases):
                try:
                    req_input = self._read(
                        "inputs/inp{}.txt".format(i+1)).strip()
                    req_output = self._read(
                        "outputs/out{}.txt".format(i+1)).strip()
                    start, end = time(), None
                    process = run("./{}".format(stem),
                                  input=req_input,
                                  capture_output=True,
                                  timeout=self.TIMELIMIT/1000)
                    end = time()
                    if process.returncode == 0:
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
                    exit(0)
                finally:
                    judged_at = strftime('%I:%M:%S %p, %d-%b-%Y', localtime())

                status = self.VERDICT_MAP[verdict]
                test = Testcase(idx=i,
                                inp=req_input,
                                out=output,
                                ans=req_output,
                                judged_at=judged_at,
                                runtime=(end-start),
                                status=status,
                                remark=remark)

                if i == 0:
                    print("+{}+".format('-'*39))
                    print("| {:^4} | {:^19} | {:^4}  | ".format('SNO', "STATUS", "RUNTIME"))
                    print("+{}+".format('-'*39))
                    print("+{}+".format('-'*39))
                test.display()
                print("+{}+".format('-'*39))
                pack.append(test)

            with open("results.dat", "wb") as results_file:
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


# driver program
model = Checker()
