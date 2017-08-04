from unittest import TestCase


# Not tryue anymore
#
# class TestAContractsPerf(TestCase):
#     def test_autoprop_contract_slow(self):
#
#         # TODO : loading PyContracts is extremely slow !!! is there a way to improve ?
#         import cProfile
#         cProfile.run('from contracts.syntax import ParseException')
#         #cProfile.run('from contracts import ContractNotRespected, contract')
#
#         print('this is extremely slow !!!')