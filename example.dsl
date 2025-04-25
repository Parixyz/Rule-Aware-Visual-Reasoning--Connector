type Sky {
  attributes: [color, pollution_level]
  objects: [Bird+, Cloud*, Sun?]
}

type Bird {
  attributes: [color, speed]
  objects: []
}

rule CheckRedBirds(sky: Sky) {
  for bird in sky.Bird do {
    if bird.color = "red" then {
      contradiction 101
    }
  }
}

rule CheckCloudCount(sky: Sky) {
  if count(sky.Cloud) > 10 then {
    contradiction 202
  }
}

scene1 = LoadScene("Folder path", Sky)
scene1.Check(start, end, [CheckRedBirds, CheckCloudCount])
