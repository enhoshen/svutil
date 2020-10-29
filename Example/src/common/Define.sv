// Copyright (C) Ganzin Technology - All Rights Reserved
// ---------------------------
// Unauthorized copying of this file, via any medium is strictly prohibited
// Proprietary and confidential
//
// Contributors
// ---------------------------
// En-Ho Shen <enhoshen@ganzin.com.tw>, 2020

`ifndef __DEFINE_SV__
`define __DEFINE_SV__

// packages

// sub-modules

`define D3 4

`ifdef TEST_PAT0
	`define TIMEOUTCYCLE 100000000
	`define MAX_IMGW 20
	`define MAX_IMGH 20
	`define MAX_KNLW 9
	`define MAX_KNLH 9
	`define PAD_MODE 1
`elsif TEST_PAT1
	`define TIMEOUTCYCLE 100000000
	`define MAX_IMGW 21
	`define MAX_IMGH 21
	`define MAX_KNLW 9
	`define MAX_KNLH 9
	`define PAD_MODE 1
`elsif TEST_PAT2
	`define TIMEOUTCYCLE 100000000
	`define MAX_IMGW 30
	`define MAX_IMGH 30
	`define MAX_KNLW 8
	`define MAX_KNLH 8
	`define PAD_MODE 1
`elsif TEST_PAT3
	`define TIMEOUTCYCLE 1000000000
	`define MAX_IMGW 100
	`define MAX_IMGH 100
	`define MAX_KNLW 10
	`define MAX_KNLH 10
	`define PAD_MODE 1
`elsif TEST_PAT4
	`define TIMEOUTCYCLE 10000000000
	`define MAX_IMGW 640
	`define MAX_IMGH 480
	`define MAX_KNLW 9
	`define MAX_KNLH 9
	`define PAD_MODE 1
`elsif TEST_PAT5
	`define TIMEOUTCYCLE 100000000
	`define MAX_IMGW 20
	`define MAX_IMGH 20
	`define MAX_KNLW 9
	`define MAX_KNLH 9
	`define PAD_MODE 0
`elsif TEST_PAT6
	`define TIMEOUTCYCLE 100000000
	`define MAX_IMGW 21
	`define MAX_IMGH 21
	`define MAX_KNLW 9
	`define MAX_KNLH 9
	`define PAD_MODE 0
`elsif TEST_PAT7
	`define TIMEOUTCYCLE 100000000
	`define MAX_IMGW 30
	`define MAX_IMGH 30
	`define MAX_KNLW 8
	`define MAX_KNLH 8
	`define PAD_MODE 0
`elsif TEST_PAT8
	`define TIMEOUTCYCLE 1000000000
	`define MAX_IMGW 100
	`define MAX_IMGH 100
	`define MAX_KNLW 10
	`define MAX_KNLH 10
	`define PAD_MODE 0
`elsif TEST_PAT9
	`define TIMEOUTCYCLE 10000000000
	`define MAX_IMGW 640
	`define MAX_IMGH 480
	`define MAX_KNLW 9
	`define MAX_KNLH 9
	`define PAD_MODE 0
`else
	`define TIMEOUTCYCLE 100
	`define ERROR_CFG
`endif

`endif //__DEFINE_SV__

