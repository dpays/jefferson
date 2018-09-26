# Jefferson
## dPay API Server (JSON-RPC)

A reverse proxy that only speaks json-rpc 2.0. Upstream routing is done using json-rpc method "namespaces".

## Installation

### Install the latest Docker Compose
```
sudo curl -L "https://github.com/docker/compose/releases/download/1.22.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Clone Jefferson and Configure

```
git clone https://github.com/dpays/jefferson.git
cd jefferson
```
- `DEV_config.json` is the main config file, we also use this configuration file in our production environments since we are still in BETA.
- You will need a server running 0.19.6 for non-appbase RPC calls and a server running 0.20.2 for appbase-based RPC calls.
- The default configuration is what we use for [dSite](https://dsite.io) and [dSocial](https://dsocial.io). You can use your own nodes or can use the default nodes operated by [dPay Nodes Team](https://dpaynodes.com).

### Launch Jefferson
```
screen
docker-compose up
```

## Public Jefferson Nodes

- dPay Primary API Node - [https://api.dpays.io/](https://api.dpayeurope.com/)
- dPay Secondary API Node - [https://dpayapi.com/](https://dpayapi.com/)
- dPayLabs' API Node - [https://api.dpayjs.com](https://api.dpayjs.com)
- dPay Europe API Node - [https://api.dpayeurope.com/](https://api.dpayeurope.com/)
- dPay USA API Node - [https://api.dpayusa.com/](https://api.dpayusa.com/)
- dPayID API Node - [https://api.dpayid.io/](https://api.dpayid.io/)
- dSite's dPay API Node - [https://dapi.dsite.io/](https://dapi.dsite.io/)

## Public RPC/WS Nodes (Public domain)
- dPay GreatChain [https://greatchain.dpaynodes.com](https://greatchain.dpaynodes.com) or ***[wss://greatchain.dpaynodes.com](wss://greatchain.dpaynodes.com)***
- dPay GreatBase [https://greatbase.dpaynodes.com](https://greatbase.dpaynodes.com) or ***[wss://greatbase.dpaynodes.com](wss://greatbase.dpaynodes.com)***
- dPay GreatChain USA [https://greatchain.dpays.io](https://greatchain.dpaynodes.io) or ***[wss://greatchain.dpays.io](wss://greatchain.dpaynodes.io)***
- dPay D [https://d.dpays.io](https://d.dpays.io) or ***[wss://d.dpays.io](wss://d.dpays.io)***
- dPay DPAYD [https://dpayd.dpays.io](https://dpayd.dpays.io) or ***[wss://dpayd.dpays.io](wss://dpayd.dpays.io)***
- dPay Chicago (dPay USA) [https://chicago.dpayusa](https://chicago.dpayusa.com) or ***[wss://chicago.dpayusa.com](wss://chicago.dpayusa.com)***
- dPay Atlanta (dPay USA) [https://atlanta.dpayusa.com](https://atlanta.dpayusa.com) or ***[wss://atlanta.dpayusa.com](wss://atlanta.dpayusa.com)***
- dPay Dallas (dPay USA) [https://dallas.dpayusa.com](https://dallas.dpayusa.com) or ***[wss://dallas.dpayusa.com](wss://dallas.dpayusa.com)***
- dPay Los Angeles (dPay USA) [https://la.dpayusa.com](https://la.dpayusa.com) or ***[wss://la.dpayusa.com](wss://la.dpayusa.com)***
- dPay San Francisco (dPay USA) [https://sf.dpayusa.com](https://sf.dpayusa.com) or ***[wss://sf.dpayusa.com](wss://sf.dpayusa.com)***
- dPay Miami (dPay USA) [https://miami.dpayusa.com](https://miami.dpayusa.com) or ***[wss://miami.dpayusa.com](wss://miami.dpayusa.com)***
- dPay Iowa (dPay USA) [https://iowa.dpayusa.com](https://iowa.dpayusa.com) or ***[wss://iowa.dpayusa.com](wss://iowa.dpayusa.com)***
- dPay Virginia (dPay USA) [https://virginia.dpayusa.com](https://virginia.dpayusa.com) or ***[wss://virginia.dpayusa.com](wss://virginia.dpayusa.com)***
- dPay Oregon (dPay USA) [https://oregon.dpayusa.com](https://oregon.dpayusa.com) or ***[wss://oregon.dpayusa.com](wss://oregon.dpayusa.com)***
- dPay South Carolina (dPay USA) [https://sc.dpayusa.com](https://sc.dpayusa.com) or ***[wss://sc.dpayusa.com](wss://sc.dpayusa.com)***
- dPay London (dPay Europe) [https://london.dpayeurope.com](https://london.dpayeurope.com) or ***[wss://london.dpayeurope.com](wss://london.dpayeurope.com)***
- dPay Paris (dPay Europe) [https://paris.dpayeurope.com](https://paris.dpayeurope.com) or ***[wss://paris.dpayeurope.com](wss://paris.dpayeurope.com)***
- dPay London (dPay Europe) [https://london.dpayeurope.com](https://london.dpayeurope.com) or ***[wss://london.dpayeurope.com](wss://london.dpayeurope.com)***
- dPay Germany (dPay Europe) [https://germany.dpayeurope.com](https://germany.dpayeurope.com) or ***[wss://germany.dpayeurope.com](wss://germany.dpayeurope.com)***
- dPay Western Europe [https://west.dpayeurope.com](https://west.dpayeurope.com) or ***[wss://west.dpayeurope.com](wss://west.dpayeurope.com)***
- dPay Sydney (dPay Australia) [https://sydney.dpayau.com](https://sydney.dpayau.com) or ***[wss://sydney.dpayau.com](wss://sydney.dpayau.com)***
- dPay Taiwan (dPay Asia) [https://taiwan.dpayasia.com](https://taiwan.dpayasia.com) or ***[wss://taiwan.dpayasia.com](wss://taiwan.dpayasia.com)***
- dPayID Node [https://d.dpayid.io](https://d.dpayid.io) or ***[wss://d.dpayid.io](wss://d.dpayid.io)***
- dSite Node [https://d.dsite.io](https://d.dsite.io) or ***[wss://d.dsite.io](wss://d.dsite.io)***
- dSocial Node [https://d.dsocial.io](https://d.dsocial.io) or ***[wss://d.dsocial.io](wss://d.dsocial.io)***
- dWiki Node [https://d.dwiki.io](https://d.dwiki.io) or ***[wss://d.dwiki.io](wss://d.dwiki.io)***

## Public RPC/WS Nodes (Witness Nodes)
- [@dpay](https://dsite.io/@dpay) [https://d.dpays.io](https://d.dpays.io) or ***[wss://d.dpays.io](wss://d.dpays.io)***
- [@jared](https://dsite.io/@jared) [https://dpayd.jrice.io](https://dpayd.jrice.io) or ***[wss://dpayd.jrice.io](wss://dpayd.jrice.io)***
- [@nomoreheroes](https://dsite.io/@nomoreheroes) [https://nomoreheroes.link](https://nomoreheroes.link) or ***[wss://nomoreheroes.link](wss://nomoreheroes.link)***
- [@cointroller](https://dsite.io/@cointroller) [https://cointroller.dpays.io](https://cointroller.dpays.io) or ***[wss://cointroller.dpays.io](wss://cointroller.dpays.io)***
- [@michaelx](https://dsite.io/@michaelx) [https://michaelx.link](https://michaelx.link) or ***[wss://michaelx.link](wss://michaelx.link)***
- [@onceuponatime](https://dsite.io/@onceuponatime) [https://indominon.com](https://indominon.com) or ***[wss://indominon.com](wss://indominon.com)***
- [@kusknee](https://dsite.io/@kusknee) [https://kusknee.dpayproducers.com](https://kusknee.dpayproducers.com) or ***[wss://kusknee.dpayproducers.com](wss://kusknee.dpayproducers.com)***
- [@cryptokong](https://dsite.io/@cryptokong) [https://kong.dpayproducers.com](https://kong.dpayproducers.com) or ***[wss://kong.dpayproducers.com](wss://kong.dpayproducers.com)***
- [@stan](https://dsite.io/@stan) [https://dpaystan.link](https://dpaystan.link) or ***[wss://dpaystan.link](wss://dpaystan.link)***
- [@lune](https://dsite.io/@lune) [https://lune.dpayproducers.com](https://lune.dpayproducers.com) or ***[wss://lune.dpayproducers.com](wss://lune.dpayproducers.com)***
- [@bossdan](https://dsite.io/@bossdan) [https://bossdan.dpayproducers.com](https://bossdan.dpayproducers.com) or ***[wss://bossdan.dpayproducers.com](wss://bossdan.dpayproducers.com)***
- [@samiam](https://dsite.io/@samiam) [https://samiam.link](https://samiam.link) or ***[wss://samiam.link](wss://samiam.link)***
- [@mbex](https://dsite.io/@mbex) [https://mbex.link](https://mbex.link) or ***[wss://mbex.link](wss://mbex.link)***
- [@nefertiti](https://dsite.io/@nefertiti) [https://nefertitibex.link](https://nefertitibex.link) or ***[wss://nefertitibex.link](wss://nefertitibex.link)***
- [@bigg](https://dsite.io/@bigg) [https://bigg.dpayproducers.com](https://bigg.dpayproducers.com) or ***[wss://bigg.dpayproducers.com](wss://bigg.dpayproducers.com)***
- [@chiraag](https://dsite.io/@chiraag) [https://chiraag.dpayproducers.com](https://chiraag.dpayproducers.com) or ***[wss://chiraag.dpayproducers.com](wss://chiraag.dpayproducers.com)***
- [@morrison](https://dsite.io/@morrison) [https://morrison.dpayproducers.com](https://morrison.dpayproducers.com) or ***[wss://morrison.dpayproducers.com](wss://morrison.dpayproducers.com)***
- [@quin](https://dsite.io/@quin) [https://quin.dpayproducers.com](https://quin.dpayproducers.com) or ***[wss://quin.dpayproducers.com](wss://quin.dpayproducers.com)***
- [@freedomfirst](https://dsite.io/@freedomfirst) [https://freedomfirst.app](https://freedomfirst.app) or ***[wss://freedomfirst.app](wss://freedomfirst.app)***
- [@tablecafe](https://dsite.io/@tablecafe) [https://tablecafe.dpayproducers.com](https://tablecafe.dpayproducers.com) or ***[wss://tablecafe.dpayproducers.com](wss://tablecafe.dpayproducers.com)***
- [@nickeles](https://dsite.io/@nickeles) [https://jackson.dpays.io](https://jackson.dpays.io) or ***[wss://jackson.dpays.io](wss://jackson.dpays.io)***

## Namespaces
A json-rpc method namespace is a json-rpc method prefix joined to the method name with a period, so a method in the "dpds" namespace begins with `dpds.` and will be forwarded to a dpds endpoint:
```
POST / HTTP/1.1
Content-Type: application/json

{
  "method": "dpds.count_operations",
  "params": {"operation":"account_creates"},
  "jsonrpc": "2.0",
  "id": 1
}
```

### Default Namespace
Any json-rpc method with no period in the method name is presumed to be in the "dpayd" namespace and will be forwarded to a dpayd endpoint:

```
POST / HTTP/1.1
Content-Type: application/json

{
  "method": "get_block",
  "params": [1],
  "jsonrpc": "2.0",
  "id": 1
}
```

## What Jefferson does
### At Startup
1. parse the upstream config and build the routing, caching, timeout data structures
1. open websocket and/or http connections to upstreams
1. initialize memory cache and open connections to redis cache
1. register route and error handlers


### Request/Response Cycle

1. validate jsonrpc request
1. convert individual jsonrpc requests into `JSONRPCRequest` objects, which add its pseudo-urn and upstream configuration
1. generate cache key (pseudo-urn for the moment)
1. if a single jsonrpc request:
   1. check in-memory cache, if miss
   1. make a redis `get` call
1. if a batch call:
   1. check in-memory cache for all keys
   1. for any misses:
     1. make a redis `mget` request for any keys not found in memory cache
1. if all data loaded from cache:
   1. merge cached data with requests to form response
   1. send response
1. if any jsonrpc call results aren't in cache:
  1. determine which upstream url and protocol (websockets or http) to use to fetch them
1. start upsteam request timers
1. fetch missing jsonrpc calls
1. end upstream response timers
1. decide if response is a valid jsonrpc response and that it is not a jsonrpc error response
1. if response is valid, and response is not a jsonrpc error response, determine the cache ttl for that jsonrpc namespace.method
1. for some calls, verify the the response is a consensus response or not, and modify cache ttl for irreversible block responses
1. return single jsonrpc response or assembled jsonrpc responses for batch requests
1. cache response in redis cache
1. cache response in memory
