`define forward( iname, srclogic , dstlogic) \
    Forward iname(\
        .*,\
        `rdyack_connect(src, srclogic),\
        `rdyack_connect(dst, dstlogic)\
    );
`define ignore( iname, srclogic , dstlogic , cond  )\
    Ignore iname(\
        .*,\
        .ignore(),\
        `rdyack_connect(src, srclogic),\
        `rdyack_connect(dst, dstlogic)\
    );
`define rrforward( iname , srclogics , dstlogic , srcN)\
    RoundRobinForward #(\
    .N(srcN)) iname(\
    .*,\
    .src_rdys(srclogics``_rdys),\
    .src_acks(srclogics``_acks),\
    `rdyack_connect(dst,dstlogic)\
    ); 
