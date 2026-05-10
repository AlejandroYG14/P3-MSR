import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import yaml
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message

# Nombres de las articulaciones del Pick & Place
ARM_JOINTS = [
    "joint_0", "joint_1", "joint_2", "joint_3",
    "joint_left_finger", "joint_right_finger"
]

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
    parser = argparse.ArgumentParser(description="Grafica el Gasto de potencia (G_parcial) vs tiempo.")
    parser.add_argument("bag", help="Ruta a la carpeta del rosbag")
    parser.add_argument("--out", default="plots/gasto_pick_place.png", help="Ruta de salida de la imagen")
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
    if "/joint_states" not in topic_types:
        raise RuntimeError("El rosbag no contiene /joint_states")

    msg_type = get_message(topic_types["/joint_states"])
    times = []
    gastos = []

    while reader.has_next():
        topic, data, bag_time_ns = reader.read_next()
        if topic != "/joint_states":
            continue

        msg = deserialize_message(data, msg_type)
        joint_index = {name: i for i, name in enumerate(msg.name)}

        # Comprobar si hay alguna articulación del brazo en este mensaje
        if not any(joint in joint_index for joint in ARM_JOINTS):
            continue

        gasto_actual = 0.0
        
        for joint in ARM_JOINTS:
            i = joint_index.get(joint)
            # Solo sumar el esfuerzo si existe y el array de efforts no está vacío
            if i is not None and i < len(msg.effort):
                gasto_actual += abs(msg.effort[i])

        times.append(stamp_to_seconds(msg, bag_time_ns))
        gastos.append(gasto_actual)

    if not times:
        raise RuntimeError("No se han encontrado esfuerzos del brazo en /joint_states")

    times = np.array(times)
    times = times - times[0]

    plt.figure(figsize=(10, 5))
    plt.plot(times, gastos, color='red', label="Gasto total")

    plt.xlabel("Tiempo [s]")
    plt.ylabel("Gasto ($G_{parcial}$)")
    plt.title("Gasto del pick and place vs Tiempo")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    print(f"Gráfica guardada en: {out_path}")

if __name__ == "__main__":
    main()