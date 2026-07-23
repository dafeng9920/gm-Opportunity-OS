# Consumer Policy Gate & Audit Runtime Foundation v0.1

Consumer governance is independent from Runtime Policy. The gate resolves only Consumer identity, declared capability, requested `READ` action, and Packet version scope. It never opens or evaluates a Packet.

Every `ConsumerAccessRuntime.decide()` call records an `ALLOW`, `DENY`, or `REVIEW_REQUIRED` Consumer Audit Event before any optional caller composition with the Packet Reader.
