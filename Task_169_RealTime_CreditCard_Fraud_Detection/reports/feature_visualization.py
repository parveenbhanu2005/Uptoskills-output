import plotly.graph_objects as go


def create_feature_chart(features):

    labels = list(features.keys())

    values = list(features.values())

    fig = go.Figure()

    fig.add_trace(

        go.Bar(

            x=labels,

            y=values

        )

    )

    return fig.to_html(full_html=False)