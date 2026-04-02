#!/usr/bin/env python3
"""
测试示例 - {项目名称}
使用pytest进行单元测试
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# 导入要测试的模块（根据实际项目调整）
# from src import process_data, visualize_data

def test_sample_data_creation():
    """测试示例数据创建功能"""
    # 创建测试数据
    dates = pd.date_range(start='2024-01-01', end='2024-01-05', freq='D')
    values = [100, 101, 102, 103, 104]
    df = pd.DataFrame({'日期': dates, '数值': values})
    
    # 验证数据形状
    assert df.shape == (5, 2)
    assert list(df.columns) == ['日期', '数值']
    
    # 验证数据类型
    assert df['日期'].dtype == 'datetime64[ns]'
    assert df['数值'].dtype == 'int64'
    
    # 验证具体数值
    assert df['数值'].iloc[0] == 100
    assert df['数值'].iloc[-1] == 104

def test_data_processing():
    """测试数据处理功能"""
    # 创建测试数据
    df = pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': [10, 20, 30, 40, 50]
    })
    
    # 示例处理：计算总和
    total = df['A'].sum()
    
    # 验证结果
    assert total == 15
    
    # 示例处理：计算平均值
    mean = df['B'].mean()
    assert mean == 30

def test_numpy_operations():
    """测试NumPy数组操作"""
    arr = np.array([1, 2, 3, 4, 5])
    
    # 测试基本运算
    assert arr.sum() == 15
    assert arr.mean() == 3.0
    assert arr.std() == pytest.approx(1.41421356, rel=1e-6)

def test_error_handling():
    """测试错误处理"""
    # 测试除以零错误
    with pytest.raises(ZeroDivisionError):
        result = 1 / 0
    
    # 测试索引错误
    lst = [1, 2, 3]
    with pytest.raises(IndexError):
        value = lst[10]

def test_file_operations(tmp_path):
    """测试文件操作（使用pytest的tmp_path fixture）"""
    # 创建临时文件
    test_file = tmp_path / "test.csv"
    
    # 写入测试数据
    df = pd.DataFrame({'x': [1, 2, 3], 'y': ['a', 'b', 'c']})
    df.to_csv(test_file, index=False)
    
    # 验证文件存在
    assert test_file.exists()
    
    # 读取并验证内容
    df_read = pd.read_csv(test_file)
    assert df_read.shape == (3, 2)
    assert list(df_read['x']) == [1, 2, 3]

def test_environment_variables():
    """测试环境变量"""
    # 设置测试环境变量
    os.environ['TEST_VAR'] = 'test_value'
    
    # 验证环境变量
    assert os.getenv('TEST_VAR') == 'test_value'
    
    # 清理
    del os.environ['TEST_VAR']

class TestDataFrameOperations:
    """DataFrame操作的测试类"""
    
    @pytest.fixture
    def sample_df(self):
        """创建样本DataFrame fixture"""
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'score': [85, 92, 78, 88, 95]
        })
    
    def test_dataframe_shape(self, sample_df):
        """测试DataFrame形状"""
        assert sample_df.shape == (5, 3)
    
    def test_dataframe_columns(self, sample_df):
        """测试DataFrame列名"""
        expected_columns = ['id', 'name', 'score']
        assert list(sample_df.columns) == expected_columns
    
    def test_dataframe_dtypes(self, sample_df):
        """测试DataFrame数据类型"""
        assert sample_df['id'].dtype == 'int64'
        assert sample_df['name'].dtype == 'object'
        assert sample_df['score'].dtype == 'int64'
    
    def test_filtering(self, sample_df):
        """测试数据筛选"""
        high_scores = sample_df[sample_df['score'] > 90]
        assert len(high_scores) == 2
        assert list(high_scores['name']) == ['Bob', 'Eve']

def test_skip_example():
    """跳过测试的示例"""
    pytest.skip("此测试被跳过，因为功能尚未实现")

@pytest.mark.parametrize("input_value,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (0, 0),
])
def test_parameterized_example(input_value, expected):
    """参数化测试示例"""
    # 示例：测试输入值的两倍
    result = input_value * 2
    assert result == expected

# 运行测试
if __name__ == "__main__":
    # 使用pytest.main()运行测试
    pytest.main(["-v", __file__])
