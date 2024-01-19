from svutil.string import String
from svutil.SVparse import SVhier

class TestString:

    mock_hier = SVhier()
    mock_hier.params.update({
        'CONSTANT_PARAM': 50,
        'SHIFT_PARAM':16,
        })
    def test_bracket(self):
        
        b = String('[3][5][7][9]').bracket_parse()
        print(b)
        assert b == ('3','5','7','9')

    def test_param(self):
        pass
        #p = String('DW  =4;') = 
        # print(ss(' happy=4;').IDParse())
        # print(sv.parameter)
        # print(ss('waddr;\n').IDParse() )
        # print(sv.LogicParse(ss(' [ $clog2(DW):0]waddr[3] [2][1];')) )
        # print(sv.Slice2num(' 13:0 '))

    def test_base(self):
        n, size = String("16'b0010").base_convert()
        assert (n,size) == ('0b0010', '16')

    def test_param(self):
        x = String("2*CONSTANT_PARAM").num_parse(self.mock_hier),
        print(self.mock_hier.params)
        assert x == 100 

    def test_shift(self):
        x = []
        x += [
            String("16<<2").num_parse(self.mock_hier),
            String("SHIFT_PARAM<<2").num_parse(self.mock_hier),
            ]
        for i in x:
            assert (i) == 64 

