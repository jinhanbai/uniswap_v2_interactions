from eth_abi.packed import encode_abi_packed
import eth_abi
from web3 import Web3

rpc = "https://mainnet.gateway.tenderly.co/1lLkc5fRLpfobYi47HejvX"


'''
Uniswap V2 Helper class
'''
class UniswapV2Helper:

    def __init__(
        self
    ):

        self.router_address = '0xEfF92A263d31888d860bD50809A8D171709b7b1c'

        # Dependencies
        self.graph_endpoint = "https://api.thegraph.com/subgraphs/name/Uniswap/exhange-eth"


    ###                             ###
    ##   GRAPH EXECUTION FUNCTIONS   ##
    ###                             ###

    def get_pools_query(
        self
    ) -> list:
        '''
            Returns queries to obtain 5000 pools
        '''

        queries = list()
        nr_queries = range(1,8,1)
        for n in nr_queries:
            skip = 1000 * (n - 1)

            query = '''{pairs(first:1000,skip:'''+ str(skip) +''',orderBy:txCount,orderDirection:desc){id,token0{id},token1{id}}}'''

            query_ = {
                'url': self.graph_endpoint,
                'query': query,
                'source': 'UniswapV2'
            }

            queries.append(query_)
        
        return queries

    def get_pair_pools_query(
        self,
        token0,
        token1
    ):
        '''
            Fetches all liquidity pools with token as token1 on Uni V2
        '''
        
        query = '''{pairs(where:{token0_in:["'''+ token0 +'''", "''' + token1 + '''"], token1_in:["'''+ token0 +'''", "''' + token1 + '''"]}){id,token0{id},token1{id}}}'''

        query_ = {
            'url': self.graph_endpoint,
            'query': query,
            'source': 'UniswapV2'
        }

        return query_
    
    def parse_pool_query(
        self,
        resp
    ):
        
        pool = dict()
        pool['source'] = 'UniswapV2'
        pool['token0'] = resp['token0']['id']
        pool['token1'] = resp['token1']['id']
        pool['tokens'] = [resp['token0']['id'],resp['token1']['id']]
        pool['pool_address'] = resp['id']

        return pool


    ###                             ###
    ##    RPC EXECUTION FUNCTION     ##
    ###                             ###

    def process_amounts_out_call(
        self,
        data
    ):
        # Decode hex response
        decoded_result = eth_abi.decode_abi(['uint256[]'], bytes.fromhex(data[2:]))

        # Modify step info 
        return decoded_result
    
    
    def process_balances_call(
        self,
        data
    ):
        # Decode hex response
        if data == '0x':
            return [0,0]
            
        decoded_result = eth_abi.decode_abi(['uint112', 'uint112', 'uint32'], bytes.fromhex(data[2:]))

        # Modify step info 
        return decoded_result
    
    def get_balances_call(
        self,
        pool_address
    ):

        data = self._get_balances_call()

        params = {
                    "jsonrpc": "2.0", "id": 1, "method": "eth_call", 
                    "params": [
                        {
                            "to": pool_address,
                            "data": data
                        },
                        "latest"
                    ]}

        url = {'url': rpc, 'params': params, 'query_type': 'post', 'request_type': 'fill_data', 'attribute': 'balances'}

        return url

    def _get_balances_call(
        self
    ):
        '''
        Low level call encoding to getReserves
        '''

        function_definition = f'getReserves()'
        function_signature = Web3.keccak(text=function_definition).hex()[:10]
        
        encodes = [
            
        ]

        encoded_args = eth_abi.encode_abi([], [])

        data = function_signature + encoded_args.hex()

        return data  
    
    def get_best_bid_call(
        self,
        amount_in,
        path
    ):
        '''
        Returns the amounts out from a UniV3 path
        '''

        data = self._get_amounts_out_call(
                                amount_in = amount_in, 
                                path = path
                            )

        params = {
                    "jsonrpc": "2.0", "id": 1, "method": "eth_call", 
                    "params": [
                        {
                            "to": self.router_address,
                            "data": data
                        },
                        "latest"
                    ]}

        url = {'url': rpc, 'params': params, 'query_type': 'post', 'request_type': 'fill_data', 'attribute': 'best_bid'}

        return url


    def get_amounts_out_call(
        self,
        amount_in,
        path
    ):
        '''
        Returns the amounts out from a UniV3 path
        '''

        data = self._get_amounts_out_call(
                                amount_in = amount_in, 
                                path = path
                            )

        params = {
                    "jsonrpc": "2.0", "id": 1, "method": "eth_call", 
                    "params": [
                        {
                            "to": self.router_address,
                            "data": data
                        },
                        "latest"
                    ]}

        url = {'url': rpc, 'params': params, 'query_type': 'post', 'request_type': 'fill_data', 'attribute': 'maker_amount'}

        return url

    def _get_amounts_out_call(
        self,
        amount_in,
        path
    ):
        '''
        Low level call encoding to getAmounts
        '''
        types = ['uint256', 'address[]']

        fields = f'{",".join(types)}'
        function_definition = f'getAmountsOut({fields})'
        function_signature = Web3.keccak(text=function_definition).hex()[:10]
        
        encodes = [
            fields
        ]

        encoded_args = eth_abi.encode_abi(types, [
            amount_in,
            path
        ])

        data = function_signature + encoded_args.hex()

        return data