from pickle import load, dump
from sys import argv, exit
from time import time, sleep, strftime, localtime
from subprocess import run, check_output, TimeoutExpired
from os.path import exists, splitext
from getpass import getpass
from os import listdir


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
        
        print("| {:^2} | {:^30} | {:^3} ms | {}".format(
            self.idx,
            self.status,
            self.runtime,
            self.remark
        ),
        end="\r\n"
    )


    def reveal(self):

        compress = (lambda x : (x[:255] + ["", "..."][len(x) > 255]))
        print("TESTCASE #{}".format(self.idx))
        print("VERDICT: {}".format(self.status))
        print("RUNTIME: {} ms".format(self.runtime))
        print("JUDGED AT: {}".format(self.judged_at))
        print("\nINPUT:\n{}".format(compress(self.input)))
        print("\nOUTPUT:\n{}".format(compress(self.output)))
        print("\nJURY'S OUTPUT:\n{}".format(compress(self.answer)))


class Checker:

    def __init__(self):
        
        self.COMPILE_CMDS = {
        ".c": "gcc {} -o {} --std=c99 -lm",
        ".cpp": "g++ {} -o {} --std=c++17"
    }

        self.VERDICT_MAP= {
        1: "\033[1;32mACCEPTED\033[0m",
        2: "\033[1;31mWRONG_ANSWER\033[0m",
        3: "\033[1;33mTIME_LIMIT_EXCEEDED\033[0m",
        4: "\033[1;31mRUNTIME_ERROR\033[0m",
    }

        if argv[1] == "set_pass":
            passwd = input("enter previous passwd: ")
            if self._get_pass() == passwd:
                self._set_pass(input("enter new passwd: "))
            else:
                print("Incorrect password. Please try again.")
        elif argv[1] == "judge":
            passwd = getpass("enter current passwd: ")
            if self._get_pass() == passwd:
                self._judge(argv[2])
            else:
                print("Incorrect password. Please try again.")
        elif argv[1] == "reveal":
            with open("results.pkl", "rb") as results_file:
                pack = load(results_file)
                results_file.close()
            pack[int(argv[2]) - 1].reveal()
        elif argv[1] == "clean":
            self._clean()


    def _get_pass(self):
        
        if not exists("pass.pkl"):
            raise Exception("password file not found!")
        with open("pass.pkl", "rb") as pass_file:
            password = load(pass_file)
            pass_file.close()
        return password

    
    def _set_pass(self, new_pass):
       
        with open("pass.pkl", "wb") as pass_file:
            dump(new_pass, pass_file)
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
        run("rm *.pkl")


    def _judge(self, fname):
        
        pack = []
        score = verdict = 0
        judged_at = remark  = None
        stem, ext = splitext(fname)
        testcases = max_score = len(listdir("inputs"))
        command = self.COMPILE_CMDS[ext].format(fname, stem)
        process = run(command)
        
        if process.returncode == 0:
            for i in range(testcases):
                try:
                    req_input = self._read("inputs/inp{}.txt".format(i+1)).strip()
                    req_output = self._read("outputs/out{}.txt".format(i+1)).strip()
                    start, end = time(), None
                    process = run("./" + stem, input=req_input, capture_output=True, timeout=2)
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
                    raise Exception("unable to fetch necessary files")
                finally:
                    judged_at = strftime('%I:%M:%S %p, %d-%b-%Y', localtime())

                status = self.VERDICT_MAP[verdict]
                test = Testcase(idx=i+1,
                                inp=req_input,
                                out=output,
                                ans=req_output,
                                judged_at=judged_at,
                                runtime=(end-start),
                                status=status,
                                remark=remark)

                if i == 0:
                    print("".join(['+', '-'*37, '+']))
                test.display()
                print("".join(['+', '-'*37, '+']))
                pack.append(test)

            with open("results.pkl", "wb") as results_file:
                dump(pack, results_file)
                results_file.close()
        else:
            print("\033[1;31mCOMPILATION_ERROR\033[0m",)


#driver program
model = Checker()