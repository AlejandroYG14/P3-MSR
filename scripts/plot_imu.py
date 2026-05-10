import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import yaml
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message

def detect_storage_id(bag_path: Path) -> str:
    metadata_file = bag_path / "metadata.yaml"
    if not metadata_file.exists():
        return "sqlite3"
    with open(metadata_file, "r") as f:
        metadata = yaml.safe_load(f)
    return metadata["rosbag2_bagfile_information"].get("storage_identifier", "sqlite3")

def stamp_to_seconds(msg, bag_time_ns: int) -> float:
    if hasattr(msg, "header"):
        stamp = msg.header.stamp
        if stamp.sec != 0 or stamp.nanosec != 0:
            return stamp.sec + stamp.nanosec * 1e-9
    return bag_time_ns * 1e-9

def main():
    parser = argparse.ArgumentParser(description="Grafica aceleracion lineal de la IMU vs tiempo.")
    parser.add_argument("bag", help="Ruta a la carpeta del rosbag")
    parser.add_argument("--out", default="plots/aceleracion_imu.png", help="Ruta de salida de la imagen")
    args = parser.parse_args()

    bag_path = Path(args.bag)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    storage_id = detect_storage_id(bag_path)

    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(uri=str(bag_path), storage_id=storage_id),
        rosbag2_py.ConverterOptions(input_serialization_format="cdr", output_serialization_format="cdr"),
    )

    topic_types = {topic.name: topic.type for topic in reader.get_all_topics_and_types()}
    if "/imu" not in topic_types:
        raise RuntimeError("El rosbag no tiene /imu")

    msg_type = get_message(topic_types["/imu"])
    times = []
    accel_x, accel_y, accel_z = [], [], []

    while reader.has_next():
        topic, data, bag_time_ns = reader.read_next()
        if topic != "/imu":
            continue

        msg = deserialize_message(data, msg_type)
        times.append(stamp_to_seconds(msg, bag_time_ns))
        accel_x.append(msg.linear_acceleration.x)
        accel_y.append(msg.linear_acceleration.y)
        accel_z.append(msg.linear_acceleration.z)

    if not times:
        raise RuntimeError("No se han encontrado mensajes en /imu.")

    times = np.array(times)
    times = times - times[0]

    plt.figure(figsize=(10, 5))
    plt.plot(times, accel_x, label="Accel X")
    plt.plot(times, accel_y, label="Accel Y")
    plt.plot(times, accel_z, label="Accel Z")

    plt.xlabel("Tiempo [s]")
    plt.ylabel("Aceleración [$m/s^2$]")
    plt.title("Aceleración lineal (IMU) vs Tiempo")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    print(f"Gráfica guardada en: {out_path}")

if __name__ == "__main__":
    main()