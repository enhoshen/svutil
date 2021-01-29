from SVutil.SVstr import SVstr
from SVutil.SVparse import SVhier

class TestSVstr:

    mock_hier = SVhier()
    mock_hier.params.update({
        'CONSTANT_PARAM': 50,
        'SHIFT_PARAM':16,
        })
    def test_bracket(self):
        
        b = SVstr('[3][5][7][9]').BracketParse()
        print(b)
        assert b == ('3','5','7','9')

    def test_param(self):
        pass
        #p = SVstr('DW  =4;') = 
        # print(ss(' happy=4;').IDParse())
        # print(sv.parameter)
        # print(ss('waddr;\n').IDParse() )
        # print(sv.LogicParse(ss(' [ $clog2(DW):0]waddr[3] [2][1];')) )
        # print(sv.Slice2num(' 13:0 '))

    def test_base(self):
        n, size = SVstr("16'b0010").BaseConvert()
        assert (n,size) == ('0b0010', '16')

    def test_param(self):
        x = SVstr("2*CONSTANT_PARAM").NumParse(self.mock_hier),
        assert x == 50

    def test_shift(self):
        x = []
        x += [
            SVstr("16<<2").NumParse(self.mock_hier),
            SVstr("SHIFT_PARAM<<2").NumParse(self.mock_hier),
            ]
        for i in x:
            assert (i) == 64 

