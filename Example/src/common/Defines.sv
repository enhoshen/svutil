// Copyright (C) Ganzin Technology - All Rights Reserved
// ---------------------------
// Unauthorized copying of this file, via any medium is strictly prohibited
// Proprietary and confidential
//
// Contributors
// ---------------------------
// En-Ho Shen <enhoshen@ganzin.com.tw>, 2020

`ifndef __DEFINES_SV__
`define __DEFINES_SV__

// packages

// sub-modules

`define D3 4
`define p_C(p) parameter _C_``p = $clog2(p)
`define p_C1(p) parameter _C1_``p = $clog2(p+1)
`define p_CC(p) parameter _CC_``p = $clog2($clog2(p))
`define p_C1C(p) parameter _C1C_``p = $clog2($clog2(p)+1)
`define p_CC1(p) parameter _CC1_``p = $clog2($clog2(p+1))
`define p_C1C1(p) parameter _C1C1_``p = $clog2($clog2(p+1)+1)
`define p_S(p) parameter _S_``p = 1<<p

`endif //__DEFINES_SV__

