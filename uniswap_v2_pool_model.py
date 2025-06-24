from utils.Uniswap.Uniswap_v2.Uniswap_v2_helper import UniswapV2Helper

UniswapV2Helper = UniswapV2Helper()

class UniswapV2Pool:

    def __init__(
        self,
        pool
    ):

        self.pool_address = pool['pool_address']
        self.tokens = sorted(pool['tokens'])
        self.source = pool['source']
        self.token0 = self.tokens[0]
        self.token1 = self.tokens[1]
        self.has_liquidity = True

        # NOTE: 
        # reference_bids is a (sell_token) => (buy_token) => (buy_token_amount) 
        # whereby the trade size is fixed and equal across all pools. 
        # The trade size is a meta parameter

        self.reserve0 = None if 'reserve0' not in pool else pool['reserve0']
        self.reserve1 = None if 'reserve1' not in pool else pool['reserve1']
        self.reference_bids = {t: dict() for t in self.tokens} if not 'reference_bids' in pool else pool['reference_bids']
    
    def has_complete_data(
        self
    ):
        
        if not self.reserve0 or not self.reserve1:
            return False
        
        return True

    def to_dict(
        self,
        deep = False
    ):
        p = dict()
        p['pool_address'] = self.pool_address
        p['source'] = self.source
        p['tokens'] = self.tokens

        if deep:
            p['reserve0'] = self.reserve0
            p['reserve1'] = self.reserve1
            p['reference_bids'] = self.reference_bids

        return p

    def get_path(
        self,
        sell_token,
        buy_token
    ):
        return [sell_token, buy_token]

    def get_reference_bid(
        self,
        token_in,
        token_out,
        amount_in
    ):
        
        if token_in == self.token0:
            reserve_in = self.reserve0
            reserve_out = self.reserve1
        else:
            reserve_in = self.reserve1
            reserve_out = self.reserve0

        _ , self.reference_bids[token_in][token_out] = self.get_amount_out(amount_in = amount_in, reserve_in = reserve_in, reserve_out = reserve_out)

    def get_amount_out(
        self,
        amount_in,
        reserve_in, 
        reserve_out
    ):
        '''
            Calculation for amount out of constant-product pools given reserves.

            Source sample:
            https://etherscan.io/address/0x7a250d5630b4cf539739df2c5dacb4c659f2488d#code 
        '''

        if not (reserve_in > 0 and reserve_out > 0):
            return 0, 0
        
        # multiply amount_in by fee
        amount_in = int(amount_in)
        amount_in_with_fee = amount_in * 9975
        fee_amount = int(amount_in * 0.0025)
        numerator = amount_in_with_fee * reserve_out
        denominator = reserve_in * 10000 + amount_in_with_fee
        amount_out = int(numerator/denominator)
        return fee_amount, amount_out
      

    def get_amount_in(
        self,
        amount_out,
        reserve_in,
        reserve_out
    ):
        '''
            Calculation for amount in of constant-product pool given reserves.

            Source sample:
            https://etherscan.io/address/0x7a250d5630b4cf539739df2c5dacb4c659f2488d
            '''
        if not (reserve_in > 0 and reserve_out > 0):
            return 0, 0

        amount_out = int(amount_out)
        numerator = reserve_in * amount_out * 10000
        denominator = (reserve_out - amount_out) * 9975
        amount_in =  (numerator / denominator) + 1
        if amount_in < 0:
            return None, None
        fee_amount = int(amount_in * 0.0025)
        
        return fee_amount, amount_in


    def process_rpc_data(
        self,
        data
    ):
        if data['attribute'] == 'balances' and data['result']:
            
            self.process_balances_call(data['result'])

        elif data['attribute'] == 'parameter' and data['result']:
            
            self.process_parameter_call(data['result'])
        
        else:

            raise Exception("### ERROR: Uknown rpc data attribute for Uni v2")
    
    def process_parameter_call(
        self,
        data
    ):
        raise Exception("### ERROR: No paramter call required for Uniswap V2 pool.")
    
    def process_balances_call(
        self,
        data
    ):

        state =  UniswapV2Helper.process_balances_call(
                                        data = data
                                    )

        
        
        self.reserve0 = state[0]
        self.reserve1 = state[1]
    
    
    def get_state_calls(
        self
    ):
        queries = list()
        query = UniswapV2Helper.get_balances_call(pool_address=self.pool_address)
        queries.append(query)

        return queries