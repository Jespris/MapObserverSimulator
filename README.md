# MapObserverSimulator
A map observing simulator with civilizations expanding and taking over other civs, using pygame.

Features:
- Event sounds and music (can be toggled on/off)
- A random world generator:
  - Generates a few continents and some islands
  - Colder at the poles represented by snow
  - Warmer at the equator represented by rainforests and deserts
- Random civilisation generator:
  - The civilisations have unique names 
  - Each civ spawns on a random location on the map
  - The civilisations will try to settle new cities and expand to aquire resources
  - A civilisation will go to war with a neighbour if the opportunity arises, and take over a city
- GUI:
  - User can click on each civilisation to see statistics about them (their name, strength, population...)
  - Event log displays current events in the world, such as new cities being founded, or wars being declared
