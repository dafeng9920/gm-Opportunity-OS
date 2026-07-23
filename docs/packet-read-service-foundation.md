# Packet Query & Read Service Foundation v0.1

`OpportunityPacketReader` is an internal, read-only service boundary:

```
PacketReadRequest -> ConsumerValidator -> PacketQueryValidator -> Reader -> OpportunityPacketStore -> PacketReadResult
```

It provides no API, policy decision, packet mutation, export, delivery, Builder, Gate, Judge, or Triad behavior. Consumers receive immutable snapshot metadata and serialized payload, never a SQLite connection.
