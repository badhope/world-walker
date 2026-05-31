import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False


class SalesForecastVisualizer:

    def __init__(self, output_dir="data/sales_forecast"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_sales_forecast(self, historical_dates, historical_values,
                            forecast_dates, forecast_values,
                            confidence_lower=None, confidence_upper=None,
                            save_name="sales_forecast.png"):
        fig, ax = plt.subplots(figsize=(14, 6))

        ax.plot(historical_dates, historical_values, color='steelblue',
                linewidth=2, label='历史数据')

        ax.plot(forecast_dates, forecast_values, color='coral',
                linewidth=2, linestyle='--', label='预测数据')

        if confidence_lower is not None and confidence_upper is not None:
            ax.fill_between(forecast_dates, confidence_lower, confidence_upper,
                            color='coral', alpha=0.2, label='置信区间')

        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('销售额', fontsize=12)
        ax.set_title('销售预测', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        save_path = self.output_dir / save_name
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"销售预测图已保存至: {save_path}")
        return save_path

    def plot_feature_importance(self, feature_importance, top_n=10,
                                save_name="feature_importance.png"):
        if not feature_importance:
            logger.warning("没有特征重要性数据可绘制")
            return None

        sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        top_features = sorted_importance[:top_n]

        features = [item[0] for item in top_features]
        importance = [item[1] for item in top_features]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(features, importance, color='steelblue')
        ax.set_xlabel('特征重要性', fontsize=12)
        ax.set_ylabel('特征', fontsize=12)
        ax.set_title(f'Top {top_n} 重要特征', fontsize=14, fontweight='bold')
        ax.invert_yaxis()

        for i, (bar, imp) in enumerate(zip(bars, importance)):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height() / 2,
                    f'{imp:.4f}', va='center', ha='left', fontsize=10)

        plt.tight_layout()
        save_path = self.output_dir / save_name
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"特征重要性图已保存至: {save_path}")
        return save_path

    def plot_model_comparison(self, model_scores, save_name="model_comparison.png"):
        if not model_scores:
            logger.warning("没有模型对比数据可绘制")
            return None

        models = list(model_scores.keys())
        r2_scores = [model_scores[m].get('r2', 0) for m in models]
        mae_scores = [model_scores[m].get('mae', 0) for m in models]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        colors_r2 = ['green' if r2 == max(r2_scores) else 'steelblue' for r2 in r2_scores]
        bars1 = ax1.bar(models, r2_scores, color=colors_r2)
        ax1.set_ylabel('R² Score', fontsize=12)
        ax1.set_title('模型 R² 对比', fontsize=14, fontweight='bold')
        ax1.tick_params(axis='x', rotation=45)

        for i, (bar, r2) in enumerate(zip(bars1, r2_scores)):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{r2:.4f}', ha='center', va='bottom', fontsize=10)

        colors_mae = ['red' if mae == min(mae_scores) else 'coral' for mae in mae_scores]
        bars2 = ax2.bar(models, mae_scores, color=colors_mae)
        ax2.set_ylabel('MAE', fontsize=12)
        ax2.set_title('模型 MAE 对比', fontsize=14, fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)

        for i, (bar, mae) in enumerate(zip(bars2, mae_scores)):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{mae:.2f}', ha='center', va='bottom', fontsize=10)

        plt.tight_layout()
        save_path = self.output_dir / save_name
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"模型对比图已保存至: {save_path}")
        return save_path

    def plot_predicted_vs_actual(self, y_true, y_pred,
                                 save_name="pred_vs_actual.png"):
        if len(y_true) != len(y_pred):
            logger.warning("真实值和预测值长度不匹配")
            return None

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(y_true, y_pred, alpha=0.6, color='steelblue')

        min_val = min(y_true.min(), y_pred.min())
        max_val = max(y_true.max(), y_pred.max())
        ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2,
                label='完美预测线')

        ax.set_xlabel('实际值', fontsize=12)
        ax.set_ylabel('预测值', fontsize=12)
        ax.set_title('预测值 vs 实际值', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        save_path = self.output_dir / save_name
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"预测对比图已保存至: {save_path}")
        return save_path

    def generate_all_plots(self, analysis_results):
        logger.info("开始生成可视化图表...")
        saved_plots = []

        if 'insights' in analysis_results and 'feature_importance' in analysis_results['insights']:
            fi = analysis_results['insights']['feature_importance'].get('all_features', {})
            plot_path = self.plot_feature_importance(dict(fi))
            if plot_path:
                saved_plots.append(plot_path)

        if 'insights' in analysis_results and 'model_comparison' in analysis_results['insights']:
            model_comp = {}
            for item in analysis_results['insights']['model_comparison']:
                model_comp[item['model']] = {'r2': item['r2'], 'mae': item['mae']}
            plot_path = self.plot_model_comparison(model_comp)
            if plot_path:
                saved_plots.append(plot_path)

        logger.info(f"可视化图表生成完成，共生成 {len(saved_plots)} 个图表")
        return saved_plots
