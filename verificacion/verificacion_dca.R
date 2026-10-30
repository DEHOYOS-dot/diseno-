# Carga el CSV de la variante del experimento, ubicado en la carpeta data del proyecto.
datos <- read.csv("../data/dca_mi_variante.csv")
# Ajusta el ANOVA de un factor; factor(secador) indica que secador es cualitativo.
modelo <- aov(humedad ~ factor(secador), data = datos)
# Anuncia que se imprimirá la tabla del análisis de varianza.
cat("Resumen del ANOVA:\n")
# Muestra las sumas de cuadrados, grados de libertad, estadístico F y valor p.
print(summary(modelo))
# Anuncia que se mostrarán las medias de humedad para cada secador.
cat("\nMedias de humedad por secador:\n")
# Calcula la media observada de humedad para cada nivel de secador.
medias_secador <- aggregate(humedad ~ secador, data = datos, FUN = mean)
# Imprime la tabla de medias para facilitar la comparación descriptiva.
print(medias_secador)
# Extrae la tabla ANOVA para obtener el cuadrado medio del error experimental.
tabla_anova <- summary(modelo)[[1]]
# Obtiene el CME de la fila residual de la tabla ANOVA.
cme <- tabla_anova["Residuals", "Mean Sq"]
# Calcula la media general de humedad como referencia para el CV.
media_general <- mean(datos$humedad)
# Calcula el coeficiente de variación: CV = sqrt(CME) / media general * 100.
cv <- sqrt(cme) / media_general * 100
# Imprime el CV como porcentaje con cuatro cifras decimales.
cat(sprintf("\nCoeficiente de variación: %.4f%%\n", cv))
# Anuncia las comparaciones de medias mediante el procedimiento de Tukey.
cat("\nComparaciones múltiples de Tukey:\n")
# Imprime diferencias, intervalos de confianza y valores p ajustados entre secadores.
print(TukeyHSD(modelo))
