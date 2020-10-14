#NICOTB=../nicotb/lib
#NICOTB=/home/enhoshen/nicotb/lib
TECH=TSMC90
IRUN=irun
TCHECK=
VERBOSE=
HOME=/home/enhoshen/research/lpAccel
#newnico
PY=python3.7
NICOTB=$(shell $(PY) -c "import nicotb; print(nicotb.__path__[0])")
PY_SUFFIX=$(shell $(PY) -c "from distutils.sysconfig import get_config_var; print(get_config_var('EXT_SUFFIX'))")
PRELOAD=$(shell $(PY) -c "from distutils.sysconfig import get_config_var; print(get_config_var('LDLIBRARY'))")
BRIDGE_SO=$(NICOTB)/bridge_vpi$(PY_SUFFIX)

#Top_syn:
#	make ARGS="+define+SDF=\\\"../$(SYN)/Top_syn.sdf\\\" +define+GATE_LEVEL +define+SRAM_GEN_MODE=SYNOPSYS32 +incdir+../$(SYN)/SAED32_EDK/lib/sram/verilog/ +incdir+../$(SYN)/SAED32_EDK/lib/stdcell_rvt/verilog/ +incdir+../$(SYN)/ +nowarn+SDFNCAP:SDFNDP:MACRDF:CUVWSP:SDFNSB:SDFNL1 " Top_test


#%: $(if $(SV),$(SV).sv,%.sv)
# macro options:
# SIM
# GATE_LEVEL
PRE := $(if$(SV),$(SV).sv, %.sv )
%: 
	PYTHONPATH='/home/enhoshen/.local/lib/python3.7/site-packages' \
	LD_PRELOAD=$(PRELOAD) PYTHONPATH=`pwd` GLOG_logtostderr=1 GLOG_minloglevel=0 NICOTB_MODE=VPI \
	TEST=$(if $(TEST),$(TEST),$@) TOPMODULE=$(if $(TOP),$(TOP),$@) \
	$(IRUN) +ncnowarn+VPISTF +access+rw -loadvpi $(BRIDGE_SO):VpiBoot \
    +incdir+/opt/CAD/cell_lib/CBDK_TSMC90GUTM_Arm_f1.0/CIC/Verilog/ \
    +define+$@ +define+HOME=$(HOME) +define+TESTMODULE=$(if $(TEST),$(TEST),$@)  \
    $(if $(HCLK) , +define+HCLK=$(HCLK) ,) $(if $(COND) , +define+COND=$(COND), ) \
    $(if $(SIM) , -seq_udp_delay 50ps +define+SIM=$(SIM),) $(if $(GATE_LEVEL) , +define+GATE_LEVEL=$(GATE_LEVEL),)\
    $(if $(GATE_LEVEL) ,  -seq_udp_delay 50ps +define+no_warning +nowarn+SDFNCAP:SDFNDP:MACRDF:CUVWSP:SDFNSB:SDFNL1,)\
    $(NICOTB)/verilog/Utils.sv $(if $(SV),$(SV) , $@.sv) +sv

# dump_scoreboard help you recording the lastest run time and result
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

clean:
	-rm -rf ncsim* novas* irun* scoreboard.db __pycache__ INCA_libs
