from datetime import date
from datetime import datetime
from typing import cast
from typing import Optional
from typing import Union

from custom_components.tapo.const import Component
from custom_components.tapo.const import DOMAIN
from custom_components.tapo.coordinators import HassTapoDeviceData
from custom_components.tapo.coordinators import TapoDataCoordinator
from custom_components.tapo.entity import CoordinatedTapoEntity
from custom_components.tapo.hub.sensor import (
    async_setup_entry as async_setup_hub_sensors,
)
from custom_components.tapo.sensors import CurrentEnergySensorSource
from custom_components.tapo.sensors import MonthEnergySensorSource
from custom_components.tapo.sensors import MonthRuntimeSensorSource
from custom_components.tapo.sensors import SignalSensorSource
from custom_components.tapo.sensors import TodayEnergySensorSource
from custom_components.tapo.sensors import TodayRuntimeSensorSource
from custom_components.tapo.sensors.tapo_sensor_source import TapoSensorSource
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

# Supported sensors: Today energy and current power
SUPPORTED_ENERGY_SENSOR = [
    CurrentEnergySensorSource,
    TodayEnergySensorSource,
    MonthEnergySensorSource,
    TodayRuntimeSensorSource,
    MonthRuntimeSensorSource,
    # TapoThisMonthEnergySensor, hotfix
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    # get tapo helper
    data = cast(HassTapoDeviceData, hass.data[DOMAIN][entry.entry_id])
    _setup_from_coordinator(hass, data.coordinator, async_add_entities)
    if data.coordinator.is_hub:
        await async_setup_hub_sensors(hass, entry, async_add_entities)


def _setup_from_coordinator(
    hass: HomeAssistant,
    coordinator: TapoDataCoordinator,
    async_add_entities: AddEntitiesCallback,
):
    sensors = [TapoSensor(coordinator, SignalSensorSource())]
    if coordinator.components.has(Component.ENERGY_MONITORING.value):
        sensors.extend(
            [TapoSensor(coordinator, factory()) for factory in SUPPORTED_ENERGY_SENSOR]
        )
    async_add_entities(sensors, True)


class TapoSensor(CoordinatedTapoEntity[TapoDataCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TapoDataCoordinator,
        sensor_source: TapoSensorSource,
    ):
        super().__init__(coordinator)
        self._sensor_source = sensor_source
        self._sensor_config = self._sensor_source.get_config()
        self._attr_entity_category = (
            EntityCategory.DIAGNOSTIC if self._sensor_config.is_diagnostic else None
        )
        self._attr_name = self._sensor_config.name.strip().title()

    @property
    def unique_id(self):
        return super().unique_id + "_" + self._sensor_config.name.replace(" ", "_")

    @property
    def device_class(self) -> Optional[str]:
        return self._sensor_config.device_class

    @property
    def state_class(self) -> Optional[str]:
        return self._sensor_config.state_class

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
        return self._sensor_config.unit_measure

    @property
    def native_value(self) -> Union[StateType, date, datetime]:
        return self._sensor_source.get_value(self.coordinator)
