    """
    Read the Excel located at `archivo_entrada` (can have multiple sheets).
    Write a new Excel to `output_path` with sheets like:
        - "Resultados" (main calculations)
        - "Alertas" (risk flags)
        - "Fórmulas" (explanations / thresholds)
    No return value required; raise exceptions for invalid input.
    """
def analizar_inventarios(archivo_entrada: str, archivo_salida: str) -> None:
"""Función principal que analiza inventarios y genera reportes."""
    try:
        xls = pd.ExcelFile(archivo_entrada)
        hojas_disponibles = xls.sheet_names

        todos_resultados = []
        todas_alertas = []

        for hoja in hojas_disponibles:
            try:
                df = pd.read_excel(archivo_entrada, sheet_name=hoja)

                if not validate_dataframe(df, hoja):
                    continue

                resultados, alertas = process_sheet(df, hoja)
                todos_resultados.extend(resultados)
                todas_alertas.extend(alertas)

            except Exception as e:
                logger.error(f"Error al procesar la hoja '{hoja}': {str(e)}", exc_info=True)
                continue

        # Crear DataFrames y guardar resultados
        save_results(todos_resultados, todas_alertas, archivo_salida)

        logger.info(f"Análisis completado. Procesadas {len(hojas_disponibles)} hojas. Resultados en '{archivo_salida}'")

    except Exception as e:
        logger.error(f"Error crítico al procesar el archivo: {str(e)}", exc_info=True)
        raise


def save_results(resultados: List[Dict], alertas: List[Dict], output_path: str) -> None:
    """Guarda los resultados en un archivo Excel."""
    df_resultados = pd.DataFrame(resultados)
    df_alertas = pd.DataFrame(alertas) if alertas else pd.DataFrame(columns=['Hoja', 'Producto', 'Mes', 'Alertas'])

    formulas = pd.DataFrame({
        'Fórmula': [
            'Ventas_mensuales =SUMA(Ventas_día_1, ..., Ventas_día_n)',
            'Compras_mensuales =SUMA(Compras_día_1, ..., Compras_día_n)',
            'Existencia_inicial = Primer valor del mes de Existencia_Inicial',
            'Final_mensual = Último valor del mes de Final Físico',
            'Variación_Neta = Final_Físico-Existencia_Inicial',
            'Rotación de inventario = Ventas/((Existencia_Inicial+Final_Físico)/2)',
            'Merma_% = (Variación_Neta/Compras)*100',
            'Valor_Merma = Variación_Neta*PRECIO PÚBLICO (M3)',
            'Desviación_% = ((Ventas-Promedio Ventas)/Promedio Ventas)*100',
            '% Uso Tanque = ((Existencia Inicial+Final Física)/2)/Capacidad Tanque*100',
            'Merma_significativa% = (Variación neta / Compras)×100 [ALERTA si < -0.5%]',
            'Infrautilización tanque = ((Exist Inicial+Exist Final)/2)/Capacidad×100 [ALERTA si < 20%]',
            'Rotación muy alta = Ventas mes/Inventario promedio [ALERTA si > 5]',
            'Aumento no justificado = Exist Final > Exist Inicial+Compras-Ventas'
        ]
    })

    with pd.ExcelWriter(output_path) as writer:
        df_resultados.to_excel(writer, sheet_name='Resultados', index=False)
        df_alertas.to_excel(writer, sheet_name='Alertas', index=False)
        formulas.to_excel(writer, sheet_name='Fórmulas', index=False)


if __name__ == "__main__":
    analizar_inventarios(
        '/Users/maxarvizuv/Desktop/ICT - TESTING/testICT/Prueba completa.xlsx',
        'Resultados_MAIN_Completo.xlsx'
    )

# If you paste a complete version of your script with the function `analizar_inventarios(...)`
# it will be auto-detected by the /process route and used instead of the default pandas formulas.
