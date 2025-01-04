for file in *.png; do
	echo "convirtiendo $file a Webp..."
	convert "$file" "${file%.png}.webp"
done

echo "conversion completada."
