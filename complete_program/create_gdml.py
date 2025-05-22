import configparser

config = configparser.ConfigParser()
config.read('simulation.config')


length = float(config['DIMENSIONS']['length_nm'])
width = float(config['DIMENSIONS']['width_nm'])
thickness = float(config['DIMENSIONS']['thickness_nm'])


scale_factor = float(config['SCALING'].get('scale_factor', '1'))
if scale_factor <= 0:
    scale_factor = 1

years = list(map(int, config['SIMULATION']['years'].split(',')))      # e.g. "2020,2025"
months = list(map(int, config['SIMULATION'].get('months', '1,12').split(',')))
days = list(map(int, config['SIMULATION'].get('days', '1,31').split(',')))


year_range = f"{years[0]}-{years[1]}"
month_range = f"{months[0]}-{months[1]}"
day_range = f"{days[0]}-{days[1]}"
fluence_filename = f"cumulative_fluence_{year_range}_{month_range}_{day_range}.txt"

with open(fluence_filename) as f:
    total_fluence = sum(float(line.split('\t')[1]) for line in f.readlines()[1:])


events_to_run = int(total_fluence *  3.6e-05* scale_factor)


length_mm = length * 1e-6
width_mm = width * 1e-6
thickness_mm = thickness * 1e-6
def format_mm(value):
    return f"{value:.8f}".rstrip('0').rstrip('.') if '.' in f"{value:.8f}" else f"{value:.8f}"

GDML_TEMPLATE = f"""<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<gdml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="../../../schema/gdml.xsd">

  <!-- MATERIALS -->
  <materials>
    <!-- Silicon -->
    <element Z="14" name="Silicon">
      <atom unit="g/mole" value="28.085"/>
    </element>
    <material name="Silicon_solid" state="solid">
      <D unit="g/cm3" value="2.33"/>
      <fraction n="1" ref="Silicon"/>
    </material>

    <!-- Copper -->
    <element Z="29" name="Copper">
      <atom unit="g/mole" value="63.546"/>
    </element>
    <material name="Copper_solid" state="solid">
      <D unit="g/cm3" value="8.96"/>
      <fraction n="1" ref="Copper"/>
    </material>

    <!-- Iron -->
    <element Z="26" name="Iron_elemental">
      <atom unit="g/mole" value="55.85"/>
    </element>
    <material name="Iron" state="solid">
      <D unit="g/cm3" value="7.6"/>
      <fraction n="1" ref="Iron_elemental"/>
    </material>

    <!-- Nitrogen -->
    <element Z="7" name="Nitrogen">
      <atom unit="g/mole" value="14.01"/>
    </element>

    <!-- Oxygen -->
    <element Z="8" name="Oxigen">
      <atom unit="g/mole" value="16"/>
    </element>

    <!-- Air -->
    <material name="Air" state="gas">
      <D unit="g/cm3" value="0.00129"/>
      <fraction n="0.7" ref="Nitrogen"/>
      <fraction n="0.3" ref="Oxigen"/>
    </material>

    <!-- Vacuum -->
    <material name="Vacuum" state="gas">
      <D unit="g/cm3" value="0.00129"/>
      <fraction n="0.7" ref="Nitrogen"/>
      <fraction n="0.3" ref="Oxigen"/>
    </material>

    <!-- Silicon Dioxide (SiO₂) -->
    <material name="SiO2" state="solid">
      <D unit="g/cm3" value="2.65"/>
      <fraction n="0.467" ref="Silicon"/>
      <fraction n="0.533" ref="Oxigen"/>
    </material>

    <!-- Aluminum -->
    <element Z="13" name="Aluminum">
      <atom unit="g/mole" value="26.98"/>
    </element>
    <material name="Aluminum_solid" state="solid">
      <D unit="g/cm3" value="2.7"/>
      <fraction n="1" ref="Aluminum"/>
    </material>
  </materials>

  <!-- OUTPUT SETTINGS -->
  <define>
    <constant name="TextOutputOn" value="1"/>
    <constant name="BriefOutputOn" value="0"/>
    <constant name="VRMLvisualizationOn" value="1"/>
    <constant name="EventsToAccumulate" value="50"/>
    <constant name="LightProducingParticle" value="0"/>
    <constant name="LowEnergyCutoff" value="0."/>
    <constant name="KeepOnlyMainParticle" value="0"/>
    <quantity name="ProductionLowLimit" type="threshold" value="100" unit="keV"/>
    <constant name="SaveSurfaceHitTrack" value="1"/>
    <constant name="SaveTrackInfo" value="1"/>
    <constant name="SaveEdepositedTotalEntry" value="1"/>
  </define>

  <!-- BEAM DEFINITION -->
  <define>
    <constant name="RandomGenSeed" value="100"/>
    <quantity name="BeamOffsetX" type="coordinate" value="0" unit="mm"/>
    <quantity name="BeamOffsetY" type="coordinate" value="0" unit="mm"/>
    <quantity name="BeamOffsetZ" type="coordinate" value="0" unit="mm"/>
    <quantity name="BeamSize" type="coordinate" value="-3" unit="mm"/>
    <quantity name="BeamEnergy" type="energy" value="-1" unit="MeV"/>
    <constant name="EventsToRun" value="{events_to_run}"/>
    <constant name="ParticleNumber" value="2212"/> <!-- Proton beam -->
    <quantity name="WorldRadius" type="length" value="0.06" unit="mm"/>
  </define>

  <!-- SOLID GEOMETRIES -->
  <solids>
    <!-- World Volume -->
    <box lunit="mm" name="world_solid" x="0.06" y="0.06" z="0.06"/>

    <!-- Gate Oxide -->
    <box lunit="mm" name="gate_oxide_solid" x="0.001" y="0.001" z="0.00001"/> <!-- 10 nm thick -->

    <!-- Channel -->
    <box lunit="mm" name="channel_solid" x="0.0005" y="0.001" z="0.000025"/> <!-- 25 nm thick -->

    <!-- Source and Drain -->
    <box lunit="mm" name="source_solid" x="0.0005" y="0.001" z="0.0001"/> <!-- 100 nm thick -->
    <box lunit="mm" name="drain_solid" x="0.0005" y="0.001" z="0.0001"/> <!-- 100 nm thick -->

    <!-- Metal Contacts -->
    <box lunit="mm" name="metal_contact_solid" x="0.0001" y="0.0001" z="0.001"/> <!-- 10 nm thick -->




    <!-- Metal Contacts -->
    <box lunit="mm" name="copper_contact_solid" x="{format_mm(length_mm)}" y="{format_mm(width_mm)}" z="{format_mm(thickness_mm)}"/>

  </solids>

  <!-- STRUCTURE -->
  <structure>
    <!-- Gate Oxide -->
    <volume name="gate_oxide_log">
      <materialref ref="SiO2"/>
      <solidref ref="gate_oxide_solid"/>
    </volume>

    <!-- Channel -->
    <volume name="channel_log">
      <materialref ref="Silicon_solid"/>
      <solidref ref="channel_solid"/>
    </volume>

    <!-- Source -->
    <volume name="source_log">
      <materialref ref="Silicon_solid"/>
      <solidref ref="source_solid"/>
    </volume>

    <!-- Drain -->
    <volume name="drain_log">
      <materialref ref="Silicon_solid"/>
      <solidref ref="drain_solid"/>
    </volume>

    <!-- Metal Contacts -->
    <volume name="metal_contact_log">
      <materialref ref="Aluminum_solid"/>
      <solidref ref="metal_contact_solid"/>
    </volume>
    <volume name="copper_contact_log">
      <materialref ref="Copper_solid"/>
      <solidref ref="copper_contact_solid"/>
    </volume>

    <!-- World Volume -->
    <volume name="world_log">
      <materialref ref="Vacuum"/>
      <solidref ref="world_solid"/>

      <!-- Gate Oxide -->
      <physvol name="det_phys0">
        <volumeref ref="copper_contact_log"/>
        <position name="copper_contact_pos" unit="mm" x="0" y="0" z="0"/> <!-- Centered in Z -->
      </physvol>


    </volume>
  </structure>

  <!-- SETUP -->
  <setup name="Default" version="1.0">
    <world ref="world_log"/>
  </setup>
</gdml>
"""


with open('copper_omni.gdml', 'w') as f:
    f.write(GDML_TEMPLATE)

print(f"GDML file written with EventsToRun = {events_to_run} and copper contact size {length}nm x {width}nm x {thickness}nm")
