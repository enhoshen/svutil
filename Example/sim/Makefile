PY?=/opt/rh/rh-python36/root/bin/python3
NICOTB=$(shell $(PY) -c "import nicotb; print(nicotb.__path__[0])")
PY_SUFFIX=$(shell $(PY) -c "from distutils.sysconfig import get_config_var as G; print(G('EXT_SUFFIX'))")
PRELOAD=$(shell $(PY) -c "import os; from distutils.sysconfig import get_config_var as G; print(os.path.join(G('LIBDIR'), G('LDLIBRARY')))")
BRIDGE_SO=$(NICOTB)/bridge_vpi$(PY_SUFFIX)
VCS?=vcs -cpp /opt/rh/devtoolset-7/root/bin/g++
export PROJECT_PATH?=../
 
%: ./%_tb.sv ./%_tb.py
	$(VCS) $(ARGS) +vpi -debug_acc+dmptf+all -debug_region+cell+encrypt \
	       -sverilog -load $(BRIDGE_SO):VpiBoot \
	       +incdir+./+$(PROJECT_PATH)/src+$(PROJECT_PATH)/include -timescale=1ns/1ns \
	       $(NICOTB)/verilog/Utils.sv $<
	LD_PRELOAD=$(PRELOAD) PYTHONPATH=./ GLOG_logtostderr=1 GLOG_minloglevel=0 NICOTB_MODE=VPI NICOTB_VCS=1 \
	TEST=$@_tb TOPMODULE=$@_tb ./simv

#####################
# add new test here #
#####################
all:
	make TEST_CFG=0 target
	make TEST_CFG=1 target 
	make TEST_CFG=3 target 
	make TEST_CFG=4 target 
gentest:
	ARGS="+define+TEST_PAT0" \
	INC=Test_include \
	TESTMODULE=TestModule \
	REGBK=TestRegbk \
	Gen.py

valtest:
	make ValMatrix ARGS="+define+TIMEOUTCYCLE=3000+TEST_PAT0" \
		TEST_CFG=SW \
		INC=ValMatrix_include \
		TOPSV=ValMatrix_tb.sv \
		REGBK=I2cMasterRegbk \
		TESTMODULE=ValMatrix

dump_scoreboard:
	@echo -e \
	".open scoreboard.db\n"\
	".header on\n"\
	".mode column\n"\
	".print ===============\n"\
	".print All Scoreboards\n"\
	".print ===============\n"\
	"select * from Scoreboard;\n"\
	".print\n"\
	".print =========\n"\
	".print All Tests\n"\
	".print =========\n"\
	"select * from Tests;\n"\
	 | sqlite3
