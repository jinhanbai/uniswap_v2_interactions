from eth_utils import keccak, to_bytes
import eth_abi
from web3 import Web3
from typing import NamedTuple
from eth_abi.packed import encode_abi_packed
import datetime
import json

'''
Class that implements the encoding of UniswapV2 interactions.

'''
class UniswapV2Encoder:

    def __init__(
        self
    ):
        
        # UniV2 addresses:
        self.factory_address = '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f'
        self.router_address = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'

        # Targets
        self._zeroex = {'target': 'zeroex', 'address': '0xdef1c0ded9bec7f1a1670819833240f027b25eff'}
        self._oneinch = {'target': '1inch', 'address': '0x1111111254fb6c44bAC0beD2854e76F90643097d'}
        self._otex = {'target': 'otex', 'address': '####'}

        # Targets dict
        self.targets = {
            'otex': '####',
            '1inch': '0x1111111254fb6c44bAC0beD2854e76F90643097d',
            'zeroex': '0xdef1c0ded9bec7f1a1670819833240f027b25eff'
        }

        # Targets ranking single swap
        self.target_ranking = ['otex', '1inch', 'zeroex']

        # Encoding dependencies
        self.resolver_contract = '0x7a359544e4031703a6149db2994afb4e324bb242'
        self.pool_init_code_hash = '0x96e8ac4277198ff8b6f785478aa9a39f403cb768dd02cbee326c3e7da348845f'
        self.min_buy_precision = 9

        self.test = True
    
    def encode_hop(
        self,
        hop,
        allowances
    ):

        it_pre = dict()
        approval = dict()
        it = dict()
        # if len(hop.pools_addresses) == 1:
            
        #     # Simulation:
        #     # https://dashboard.tenderly.co/felixjff/project/simulator/26f3c434-81e2-4f7c-b137-7977935affd9/gas-usage

        #     it_pre = self.encode_sell_transfer(hop)
        #     it = self.encode_hop_single_pool(hop)

        #     if self.test:
        #         print("### INFO: Encoder -> Encoded UniswapV2 interaction for settlement.")
        
        # else:
            
        approval, it = self.encode_hop_multiple_pools(hop, allowances)
        
        return it_pre, approval, it
    
    def encode_sell_transfer(
        self,
        hop
    ):

        # Get pool
        pool_address = hop.pools_addresses[0]

        data = self._get_transfer(
                            value = hop.exec_sell_amount,
                            to = pool_address
                        )
        
        # Get input(s) for tx record
        inputs = list()
        inp = {'token': hop.sell_token, 'amount': str(hop.exec_sell_amount)}
        inputs.append(inp)

        # Get output(s)
        outputs = list()
        outp = {'token': hop.buy_token, 'amount': str(hop.exec_buy_amount)}
        outputs.append(outp)
        
        tx = {
            "target": hop.sell_token,
            "data": data,
            "inputs": inputs,
            "outputs": outputs
        }

        return tx
    
    def _get_transfer(
        self,
        value,
        to
    ):

        # Field types
        types = ['address', 'uint256'] # (to, value)

        # Fields
        fields = f'{",".join(types)}'

        # Function
        function_definition = f'transfer({fields})'

        # Function signature
        function_signature = Web3.keccak(text=function_definition).hex()[:10]

        # Prepare inputs
        order_paramters = [
            Web3.toChecksumAddress(to),
            int(value)
        ]


        # Encode inputs
        encoded_args = eth_abi.encode_abi(
                            ['address', 'uint256'], 
                            [Web3.toChecksumAddress(to), int(value)]
                        )

        # Get call data
        calldata = function_signature + encoded_args.hex() 

        return calldata
    
    def encode_hop_single_pool(
        self,
        hop
    ):
        '''
            Function implements new method to encode UniV2 swaps based on the Flash Swap
            functionality:
            https://docs.uniswap.org/contracts/v2/guides/smart-contract-integration/using-flash-swaps
        '''

        # Field types
        types = ['uint256', 'uint256', 'address', 'bytes']

        # Fields
        fields = f'{",".join(types)}'

        # Function
        function_definition = f'swap({fields})'

        # Function signature
        function_signature = Web3.keccak(text=function_definition).hex()[:10]
        
        tokens = sorted(hop.pools_utils)

        # Tokens
        token0 = Web3.toChecksumAddress(tokens[0])
        token1 = Web3.toChecksumAddress(tokens[1])

        # Pool
        pool_address = hop.pools_addresses[0]

        # Amounts
        if token0.lower() == hop.sell_token.lower():
            amount_1_out = int(hop.exec_buy_amount)
            amount_0_out = 0
        else:
            amount_0_out = int(hop.exec_buy_amount)
            amount_1_out = 0
        
        data = '0x'
        
        # Field encoding
        encodes = [
            fields
        ]

        # Encode parameters
        encoded_args = eth_abi.encode_abi(types, [
            amount_0_out,                   # amout0Oout
            amount_1_out,                   # amout1Oout
            Web3.toChecksumAddress(self.resolver_contract),     # receiver
            Web3.toBytes(hexstr=data)       # data
        ])

        # Encoded function + paramters
        calldata = function_signature + encoded_args.hex()

        # Get input(s) for tx record
        inputs = list()
        inp = {'token': hop.sell_token, 'amount': str(hop.exec_sell_amount)}
        inputs.append(inp)

        # Get output(s)
        outputs = list()
        outp = {'token': hop.buy_token, 'amount': str(hop.exec_buy_amount)}
        outputs.append(outp)

        tx = {
            "target": Web3.toChecksumAddress(pool_address),
            "data": calldata,
            "inputs": inputs,
            "outputs": outputs
        }

        return tx

    def encode_hop_multiple_pools(
        self,
        hop,
        allowances
    ):

        ranking = self.target_ranking

        approval = dict()
        it = self.encode(target = '1inch', hop = hop)
        

        print("### INFO: Encoder -> Encoded UniswapV2 interaction.")
        
        return approval, it

    def encode(
        self,
        target,
        hop,
    ):

        if target == 'otex':
            it = self.encode_otex(hop)
        elif target == 'zeroex':
            it = self.encode_zeroex(hop)
        elif target == '1inch':
            it = self.encode_oneinch(hop)
        
        return it
    
    def encode_otex(
        self,
        hop
    ):

        it = self.OtexTokenForToken(hop)

        return it
    
    def encode_zeroex(
        self,
        hop
    ):
        it = self.ZeroExTokenForToken(hop)

        return it
    
    def encode_oneinch(
        self,
        hop
    ):
        it = self.OneInchTokenForToken(hop)

        return it
    
    def OtexTokenForToken(
        self,
        hop
    ):
        '''
        Uses 1inch's unoswap function to settle trade against Uniswap v2.

        Source: https://etherscan.io/address/0x1111111254fb6c44bac0bed2854e76f90643097d
        '''

        # Field types
        types = ['address', 'uint256', 'uint256', 'bytes32[]']

        # Fields
        fields = f'{",".join(types)}'

        # Function
        function_definition = f'unoswap({fields})'

        # Function signature
        function_signature = Web3.keccak(text=function_definition).hex()[:10]

        # Field value pre-process
        # Source token
        src_token = Web3.toChecksumAddress(hop.sell_token)
        # Sell amount
        amount = int(hop.exec_sell_amount)
        # Minimum buy amount
        buy_amount = int(hop.exec_buy_amount)
        min_buy_amount = int(round(buy_amount - (buy_amount * hop.slippage),0))

        # Get new amount that satisfies precision
        if len(hex(min_buy_amount)) > self.min_buy_precision:
            # Get original hex
            hex_old = hex(min_buy_amount)
            # Get core of new hex
            hex_new = hex_old[:self.min_buy_precision]
            # Get precision change accounting for '0x'
            precision_change = len(hex_old) - self.min_buy_precision  
            hex_new = hex_new + '0'*precision_change
            # Get new min buy amount
            min_buy_amount = int(hex_new, 16)

        # Pools
        i = 1
        pools = list()
        while i < len(hop.pools_utils):
            tokenA = Web3.toChecksumAddress(hop.pools_utils[i-1])
            tokenB = Web3.toChecksumAddress(hop.pools_utils[i])
            pool_address = self._to_pool(tokenA, tokenB)
            pool_bytes = Web3.toBytes(hexstr=pool_address)
            pools.append(pool_bytes)
            i+=1
        
        # Field encoding
        encodes = [
            fields
        ]

        # Encode parameters
        encoded_args = eth_abi.encode_abi(types, [
            src_token,          # srcToken
            amount,             # Amount
            min_buy_amount,         # minReturn
            pools               # pools
        ])

        # Encoded function + paramters
        calldata = function_signature + encoded_args.hex()

        # Get input(s) for tx record
        inputs = list()
        inp = {'token': hop.sell_token, 'amount': str(hop.exec_sell_amount)}
        inputs.append(inp)

        # Get output(s)
        outputs = list()
        outp = {'token': hop.buy_token, 'amount': str(hop.exec_buy_amount)}
        outputs.append(outp)

        tx = {
            "target": Web3.toChecksumAddress(self._otex['address']),
            "data": calldata,
            "inputs": inputs,
            "outputs": outputs
        }

        return tx
    
    def OneInchTokenForToken(
        self,
        hop
    ):
        '''
        Uses 1inch's unoswap function to settle trade against Uniswap v2.

        Source: https://etherscan.io/address/0x1111111254fb6c44bac0bed2854e76f90643097d
        '''

        # Field types
        types = ['address', 'uint256', 'uint256', 'bytes32[]']

        # Fields
        fields = f'{",".join(types)}'

        # Function
        function_definition = f'unoswap({fields})'

        # Function signature
        function_signature = Web3.keccak(text=function_definition).hex()[:10]

        # Field value pre-process
        # Source token
        src_token = Web3.toChecksumAddress(hop.sell_token)
        # Sell amount
        amount = int(hop.exec_sell_amount)
        # Minimum buy amount
        buy_amount = int(hop.exec_buy_amount)
        min_buy_amount = int(round(buy_amount - (buy_amount * hop.slippage),0))

        # Get new amount that satisfies precision
        if len(hex(min_buy_amount)) > self.min_buy_precision:
            # Get original hex
            hex_old = hex(min_buy_amount)
            # Get core of new hex
            hex_new = hex_old[:self.min_buy_precision]
            # Get precision change accounting for '0x'
            precision_change = len(hex_old) - self.min_buy_precision  
            hex_new = hex_new + '0'*precision_change
            # Get new min buy amount
            min_buy_amount = int(hex_new, 16)

        # Pools
        i = 1
        pools = list()
        while i < len(hop.pools_utils):
            tokenA = Web3.toChecksumAddress(hop.pools_utils[i-1])
            tokenB = Web3.toChecksumAddress(hop.pools_utils[i])
            pool_address = self._to_pool(tokenA, tokenB)
            pool_bytes = Web3.toBytes(hexstr=pool_address)
            pools.append(pool_bytes)
            i+=1
        
        # Field encoding
        encodes = [
            fields
        ]

        # Encode parameters
        encoded_args = eth_abi.encode_abi(types, [
            src_token,          # srcToken
            amount,             # Amount
            min_buy_amount,         # minReturn
            pools               # pools
        ])

        # Encoded function + paramters
        calldata = function_signature + encoded_args.hex()

        # Get input(s) for tx record
        inputs = list()
        inp = {'token': hop.sell_token, 'amount': str(hop.exec_sell_amount)}
        inputs.append(inp)

        # Get output(s)
        outputs = list()
        outp = {'token': hop.buy_token, 'amount': str(hop.exec_buy_amount)}
        outputs.append(outp)

        tx = {
            "target": Web3.toChecksumAddress(self._oneinch['address']),
            "data": calldata,
            "inputs": inputs,
            "outputs": outputs
        }

        return tx
    
    def ZeroExTokenForToken(
        self,
        hop
    ) -> list:
        '''
        Uses ZeroEx's sellToUniswap (in contract 0xf9b30557AfcF76eA82C04015D80057Fa2147Dfa9) 
        to swap a token in Uniswap v2 along the route specified by the token address path.

        Source: https://etherscan.io/address/0xf9b30557afcf76ea82c04015d80057fa2147dfa9
        '''

        # Field types
        types = ['address[]', 'uint256', 'uint256', 'bool']

        # Fields
        fields = f'{",".join(types)}'

        # Function
        function_definition = f'sellToUniswap({fields})'

        # Function signature
        function_signature = Web3.keccak(text=function_definition).hex()[:10]

        # Fields values prepocessing
        # Addresses
        address_input = hop.pools_utils
        
        # minBuyAmount
        buy_amount = int(hop.exec_buy_amount)
        min_buy_amount = int(round(buy_amount - (buy_amount * hop.slippage),0))

        # Get new amount that satisfies precision
        if len(hex(min_buy_amount)) > self.min_buy_precision:
            # Get original hex
            hex_old = hex(min_buy_amount)
            # Get core of new hex
            hex_new = hex_old[:self.min_buy_precision]
            # Get precision change accounting for '0x'
            precision_change = len(hex_old) - self.min_buy_precision  
            hex_new = hex_new + '0'*precision_change
            # Get new min buy amount
            min_buy_amount = int(hex_new, 16)

        # Field encoding
        encodes = [
            fields
        ]

        # Encode parameters
        encoded_args = eth_abi.encode_abi(types, [
            address_input,          # tokens
            int(hop.exec_sell_amount), # sellAmount
            min_buy_amount,         # minBuyAmount
            False                   # isSushi
        ])

        # Encoded function + paramters
        calldata = function_signature + encoded_args.hex()

        # Get input(s) for tx record
        inputs = list()
        inp = {'token': hop.sell_token, 'amount': str(hop.exec_sell_amount)}
        inputs.append(inp)

        # Get output(s)
        outputs = list()
        outp = {'token': hop.buy_token, 'amount': str(hop.exec_buy_amount)}
        outputs.append(outp)

        tx = {
            "target": Web3.toChecksumAddress(self._zeroex['address']),
            "data": calldata,
            "inputs": inputs,
            "outputs": outputs
        }

        return tx

    def _to_pool(
        self,
        token0,
        token1
    ):
        '''
        Gets an UniV2 pool address from pool information. 

        Sources: 
        https://stackoverflow.com/questions/69472821/compute-uniswap-3-0-pool-pair-address-via-python3
        https://github.com/Uniswap/v3-sdk/blob/aeb1b09/src/utils/computePoolAddress.ts#L7
        https://stackoverflow.com/questions/66710238/compute-uniswap-pair-address-via-python
        '''
        # NOTE:
        # The function expects checksum adresses, not strings.
        one_to_zero = False
        if int(token0,16)<int(token1,16):
            abiEncoded_1 = encode_abi_packed(['address', 'address'], (token0.lower(), token1.lower()))
        else:
            one_to_zero = True
            abiEncoded_1 = encode_abi_packed(['address', 'address'], (token1.lower(), token0.lower() ))

        salt = Web3.solidityKeccak(['bytes'], ['0x' + abiEncoded_1.hex()])

        abiEncoded_2 = encode_abi_packed(['address', 'bytes32'], (self.factory_address, salt))
        
        resPair = Web3.solidityKeccak(['bytes','bytes'], ['0xff' + abiEncoded_2.hex(), self.pool_init_code_hash])[12:]

        resPair = Web3.toChecksumAddress(resPair)


        if one_to_zero:

            # NOTE:
            # if not one_to_zero, uniswop expects the following additional 
            # hex component.
            # Source: https://dashboard.tenderly.co/felixjff/project/simulator/1752ed64-20a8-4634-98db-c0c8709c3310/debugger?trace=0.6.0

            resPair = '0x' + '80000000000000003b6d0340' +  Web3.toChecksumAddress(resPair)[2:]
        
        else:

            # NOTE:
            # if not one_to_zero, uniswop expects the following additional 
            # hex component.
            # Source: https://dashboard.tenderly.co/felixjff/project/simulator/f66546e6-47f8-40bf-afe7-aff195cfa82b/debugger?trace=0.8.0

            resPair = '0x' + '00000000000000003b6d0340' +  Web3.toChecksumAddress(resPair)[2:]

        return resPair


'''
### TESTS ###

I. sellToUniswap TEST

Description: 
The idea was to compare the execution of our encoding of sellToUniswap against the execution via ZeroEx's proxy contract.

Outputs: 

Direct 1
https://dashboard.tenderly.co/felixjff/project/simulator/907d2e1d-169b-469a-9da7-e8f4650c1685/gas-usage
https://etherscan.io/tx/0xafbed35e931d0864a068918d9fbe7b746476374ac6238038d13b009b9f8b2466
Proxy 1
https://dashboard.tenderly.co/felixjff/project/simulator/5f07a17f-3c5d-44e6-ad92-564b5e0d0659/gas-usage

Result: 
Smart (direct) execution is approximately 6k gas cheaper than naive execution via ZeroEx


II. ZeroEx vs 1inch

Description:
The idea is to compare the execution of our encoding of sellToUniswap against whatever function is being implemented by 1inch.

Output:
- ZeroEx: https://dashboard.tenderly.co/felixjff/project/simulator/4088f4a9-0cea-49c0-82fb-640e04fa2df6/gas-usage
- 1inch: https://dashboard.tenderly.co/felixjff/project/simulator/54cca6cb-50d0-4a8d-85c6-6caf79cb2514/gas-usage

Result:
1inch is cheaper than ZeroEx even if we would execute ZeroEx's sellToUniswap function directly.


III. Slippage control

Description:
We want to make sure the slippage parameters are properly implemented.

Output:
https://dashboard.tenderly.co/felixjff/project/simulator/f2af47dd-30f0-495e-ad58-8ba7ee976c17/gas-usage

Result:
Success



APPENDIX

A.I. SORTING TEST

Input: [0x3472a5a71965499acd81997a54bba8d852c6e53d, 0x2260fac5e5542a773aa44fbcfedf7c193bc2c599]

Expected encodedPacked: 0x2260fac5e5542a773aa44fbcfedf7c193bc2c5993472a5a71965499acd81997a54bba8d852c6e53d
Result EncodedPacked:   0x2260fac5e5542a773aa44fbcfedf7c193bc2c5993472a5a71965499acd81997a54bba8d852c6e53d

Expected Output: [0x2260fac5e5542a773aa44fbcfedf7c193bc2c599, 0x3472a5a71965499acd81997a54bba8d852c6e53d]


A.II. unoswap TEST

Description:
Generate successful settlements with the implementation of unoswap

Outputs:
https://dashboard.tenderly.co/felixjff/project/simulator/46a980f0-1a21-4534-8d69-2dbdac5a7fd5/gas-usage


'''



'''

Example: Interaction with Smart Contract function

rfq_order_field_types = [
    "address",
    "address",
    "uint128",
    "uint128",
    "address",
    "address",
    "address",
    "bytes32",
    "uint64",
    "uint256",
]

# 0x RFQ interaction
rfq_order_field_tuple = f'({",".join(rfq_order_field_types)})'
signature_field_tuple = '(uint8,uint8,bytes32,bytes32)'

def get_fillable_rfq_order(client, exchange_proxy, gas_price, taker_address, order, v, r, s, fill_amount):
    
    rfq_order_field_tuple = f'({",".join(rfq_order_field_types)})'

    function_definition = f'fillRfqOrder({rfq_order_field_tuple},{signature_field_tuple},uint128)'
    function_signature = web3.Web3.keccak(text=function_definition).hex()[:10]

    encodes = [
        rfq_order_field_tuple,
        signature_field_tuple,
        'uint128'
    ]
    encoded_args = eth_abi.encode_abi(encodes, [[
        client.toChecksumAddress(order.makerToken),
        client.toChecksumAddress(order.takerToken),
        order.makerAmount,
        order.takerAmount,
        client.toChecksumAddress(order.maker),
        client.toChecksumAddress(order.taker),
        client.toChecksumAddress(order.txOrigin),
        int_to_32_big_endian_bytes(order.pool),
        order.expiry,
        order.salt
    ], [3, v, r, s], fill_amount])
    calldata = function_signature + encoded_args.hex()


    tx = {
        "from": taker_address,
        "to": client.toChecksumAddress(exchange_proxy),
        "data": calldata,
        "gasPrice": gas_price,
        "gas": 500_000,
        "nonce": client.eth.getTransactionCount(taker_address),
    }

    return tx

'''
